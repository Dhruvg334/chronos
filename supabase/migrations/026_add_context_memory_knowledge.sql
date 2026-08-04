-- Attributable memory, document knowledge, hybrid retrieval, and bounded context packs.

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE public.memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    project_id UUID,
    category TEXT NOT NULL CHECK (category IN ('preference','constraint','working_pattern','project_fact','personal_rule','decision')),
    content TEXT NOT NULL CHECK (length(content) BETWEEN 1 AND 4000),
    source_type TEXT NOT NULL CHECK (source_type IN ('user','reflection','document','project','planning','system')),
    source_reference JSONB NOT NULL DEFAULT '{}'::JSONB CHECK (pg_column_size(source_reference) <= 4096),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    is_explicit BOOLEAN NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proposed','confirmed','rejected','archived','expired')),
    effective_date DATE,
    review_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    content_fingerprint TEXT NOT NULL CHECK (length(content_fingerprint) = 64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id),
    FOREIGN KEY (project_id, user_id) REFERENCES public.projects(id, user_id) ON DELETE SET NULL (project_id)
);

CREATE UNIQUE INDEX memory_items_active_fingerprint_idx
    ON public.memory_items(user_id, content_fingerprint)
    WHERE status IN ('proposed','confirmed');
CREATE INDEX memory_items_user_category_idx ON public.memory_items(user_id, category, status, updated_at DESC);

CREATE TABLE public.knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    project_id UUID,
    source_type TEXT NOT NULL CHECK (source_type IN ('note','document','pasted_text','project_context')),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 240),
    status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing','ready','failed','archived')),
    original_metadata JSONB NOT NULL DEFAULT '{}'::JSONB CHECK (pg_column_size(original_metadata) <= 8192),
    checksum TEXT NOT NULL CHECK (length(checksum) = 64),
    failure_code TEXT CHECK (failure_code IS NULL OR length(failure_code) <= 80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id),
    FOREIGN KEY (project_id, user_id) REFERENCES public.projects(id, user_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX knowledge_sources_user_checksum_idx
    ON public.knowledge_sources(user_id, checksum, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'::UUID))
    WHERE status <> 'archived';
CREATE INDEX knowledge_sources_user_project_idx ON public.knowledge_sources(user_id, project_id, created_at DESC);

CREATE TABLE public.knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    project_id UUID,
    content TEXT NOT NULL CHECK (length(content) BETWEEN 1 AND 8000),
    embedding extensions.vector(384) NOT NULL,
    lexical_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    token_count INTEGER NOT NULL CHECK (token_count BETWEEN 1 AND 4096),
    position INTEGER NOT NULL CHECK (position >= 0),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB CHECK (pg_column_size(metadata) <= 4096),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, position),
    FOREIGN KEY (source_id, user_id) REFERENCES public.knowledge_sources(id, user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, user_id) REFERENCES public.projects(id, user_id) ON DELETE CASCADE
);

CREATE INDEX knowledge_chunks_user_project_idx ON public.knowledge_chunks(user_id, project_id, source_id);
CREATE INDEX knowledge_chunks_lexical_idx ON public.knowledge_chunks USING GIN(lexical_vector);
CREATE INDEX knowledge_chunks_embedding_idx ON public.knowledge_chunks USING hnsw (embedding extensions.vector_cosine_ops);

CREATE TABLE public.context_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL CHECK (purpose IN ('daily_planning','weekly_planning','project_planning','recovery','stuck','reflection')),
    entity_references JSONB NOT NULL DEFAULT '{}'::JSONB CHECK (pg_column_size(entity_references) <= 8192),
    source_references JSONB NOT NULL DEFAULT '[]'::JSONB CHECK (pg_column_size(source_references) <= 32768),
    generated_summary TEXT NOT NULL CHECK (length(generated_summary) <= 12000),
    provenance JSONB NOT NULL DEFAULT '[]'::JSONB CHECK (pg_column_size(provenance) <= 32768),
    token_count INTEGER NOT NULL CHECK (token_count BETWEEN 0 AND 8192),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL CHECK (expires_at > created_at)
);
CREATE INDEX context_packs_user_purpose_idx ON public.context_packs(user_id, purpose, created_at DESC);

CREATE TRIGGER update_memory_items_modtime BEFORE UPDATE ON public.memory_items FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_knowledge_sources_modtime BEFORE UPDATE ON public.knowledge_sources FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

ALTER TABLE public.memory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.context_packs ENABLE ROW LEVEL SECURITY;

CREATE POLICY memory_items_owner_all ON public.memory_items FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY knowledge_sources_owner_all ON public.knowledge_sources FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY knowledge_chunks_owner_all ON public.knowledge_chunks FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY context_packs_owner_all ON public.context_packs FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

REVOKE ALL ON public.memory_items, public.knowledge_sources, public.knowledge_chunks, public.context_packs FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.memory_items, public.knowledge_sources, public.context_packs TO authenticated;
GRANT ALL ON public.memory_items, public.knowledge_sources, public.knowledge_chunks, public.context_packs TO service_role;

-- Chunks and embeddings are deliberately not granted to browser roles. Retrieval returns safe excerpts only.
CREATE OR REPLACE FUNCTION public.ingest_knowledge_source_transaction(
    p_user_id UUID,
    p_idempotency_key TEXT,
    p_source JSONB,
    p_chunks JSONB
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $$
DECLARE
    v_source_id UUID := (p_source->>'id')::UUID;
    v_project_id UUID := NULLIF(p_source->>'project_id','')::UUID;
    v_existing UUID;
    v_chunk JSONB;
    v_result JSONB;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' AND auth.uid() IS DISTINCT FROM p_user_id THEN
        RAISE EXCEPTION 'ownership validation failed' USING ERRCODE = '42501';
    END IF;
    IF p_idempotency_key IS NULL OR length(p_idempotency_key) < 8
       OR jsonb_typeof(p_chunks) <> 'array' OR jsonb_array_length(p_chunks) = 0 THEN
        RAISE EXCEPTION 'invalid ingestion request' USING ERRCODE = '22023';
    END IF;
    IF v_project_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.projects WHERE id = v_project_id AND user_id = p_user_id
    ) THEN RAISE EXCEPTION 'project not owned' USING ERRCODE = '42501'; END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended(p_user_id::TEXT || ':knowledge:' || p_idempotency_key, 0));
    SELECT result_json INTO v_result FROM public.operation_receipts
      WHERE user_id = p_user_id AND operation_type = 'knowledge_ingestion' AND idempotency_key = p_idempotency_key;
    IF v_result IS NOT NULL THEN RETURN v_result || '{"idempotent_replay":true}'::JSONB; END IF;

    SELECT id INTO v_existing FROM public.knowledge_sources
      WHERE user_id = p_user_id AND checksum = p_source->>'checksum'
        AND project_id IS NOT DISTINCT FROM v_project_id AND status <> 'archived' LIMIT 1;
    IF v_existing IS NOT NULL THEN
        v_result := jsonb_build_object('status','duplicate','source_id',v_existing,'chunk_count',0,'idempotent_replay',false);
    ELSE
        INSERT INTO public.knowledge_sources(id,user_id,project_id,source_type,title,status,original_metadata,checksum)
        VALUES(v_source_id,p_user_id,v_project_id,p_source->>'source_type',p_source->>'title','processing',
               COALESCE(p_source->'original_metadata','{}'::JSONB),p_source->>'checksum');
        FOR v_chunk IN SELECT value FROM jsonb_array_elements(p_chunks) LOOP
            IF jsonb_array_length(v_chunk->'embedding') <> 384 THEN
                RAISE EXCEPTION 'embedding dimension mismatch' USING ERRCODE = '22023';
            END IF;
            INSERT INTO public.knowledge_chunks(id,source_id,user_id,project_id,content,embedding,token_count,position,metadata)
            VALUES((v_chunk->>'id')::UUID,v_source_id,p_user_id,v_project_id,v_chunk->>'content',
                   ((v_chunk->'embedding')::TEXT)::extensions.vector,(v_chunk->>'token_count')::INTEGER,
                   (v_chunk->>'position')::INTEGER,COALESCE(v_chunk->'metadata','{}'::JSONB));
        END LOOP;
        UPDATE public.knowledge_sources SET status='ready' WHERE id=v_source_id AND user_id=p_user_id;
        v_result := jsonb_build_object('status','ready','source_id',v_source_id,'chunk_count',jsonb_array_length(p_chunks),'idempotent_replay',false);
    END IF;
    INSERT INTO public.operation_receipts(user_id,operation_type,idempotency_key,result_json)
    VALUES(p_user_id,'knowledge_ingestion',p_idempotency_key,v_result);
    RETURN v_result;
EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE='42501' THEN RAISE; END IF;
    RETURN jsonb_build_object('status','failed','error_code','knowledge_ingestion_rolled_back');
END;
$$;

REVOKE ALL ON FUNCTION public.ingest_knowledge_source_transaction(UUID,TEXT,JSONB,JSONB) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ingest_knowledge_source_transaction(UUID,TEXT,JSONB,JSONB) TO service_role;

CREATE OR REPLACE FUNCTION public.retrieve_knowledge_chunks(
    p_user_id UUID,
    p_query TEXT,
    p_query_embedding extensions.vector(384),
    p_project_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 8
) RETURNS TABLE(
    chunk_id UUID, source_id UUID, project_id UUID, title TEXT, source_type TEXT,
    excerpt TEXT, score DOUBLE PRECISION, dense_rank BIGINT, lexical_rank BIGINT, created_at TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog
AS $$
    WITH eligible AS (
        SELECT c.id,c.source_id,c.project_id,c.content,c.created_at,s.title,s.source_type,
               row_number() OVER (ORDER BY c.embedding OPERATOR(extensions.<=>) p_query_embedding, c.id) AS dense_rank,
               CASE WHEN c.lexical_vector @@ websearch_to_tsquery('simple', p_query)
                    THEN row_number() OVER (ORDER BY ts_rank_cd(c.lexical_vector, websearch_to_tsquery('simple', p_query)) DESC, c.id)
               END AS lexical_rank
        FROM public.knowledge_chunks c
        JOIN public.knowledge_sources s ON s.id=c.source_id AND s.user_id=c.user_id
        WHERE c.user_id=p_user_id AND s.status='ready' AND (p_project_id IS NULL OR c.project_id=p_project_id)
    )
    SELECT id,source_id,project_id,title,source_type,left(content,600),
           (1.0/(60+dense_rank) + CASE WHEN lexical_rank IS NULL THEN 0 ELSE 1.0/(60+lexical_rank) END
            + CASE source_type WHEN 'project_context' THEN 0.004 WHEN 'note' THEN 0.002 ELSE 0 END)::DOUBLE PRECISION,
           dense_rank,lexical_rank,created_at
    FROM eligible ORDER BY 7 DESC, id LIMIT LEAST(GREATEST(p_limit,1),20);
$$;

REVOKE ALL ON FUNCTION public.retrieve_knowledge_chunks(UUID,TEXT,extensions.vector,UUID,INTEGER) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.retrieve_knowledge_chunks(UUID,TEXT,extensions.vector,UUID,INTEGER) TO service_role;

COMMENT ON TABLE public.memory_items IS 'Inspectable explicit and proposed memory with provenance; raw reasoning is prohibited.';
COMMENT ON COLUMN public.knowledge_chunks.embedding IS 'Backend-only retrieval vector; never exposed through browser API responses.';
