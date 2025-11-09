-- Volunteer Hub Database Schema
-- Requires PostgreSQL with PostGIS extension

-- Enable PostGIS for geographic operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ======================
-- CORE ENTITIES
-- ======================

-- Persons (community members, kupuna, volunteers)
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(255),
    languages TEXT[] DEFAULT '{"en"}',
    location GEOGRAPHY(POINT, 4326),
    preferences JSONB DEFAULT '{}',
    agent_state JSONB DEFAULT '{}', -- Persistent agent memory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction TIMESTAMPTZ DEFAULT NOW()
);

-- Resources (gardens, kitchens, vehicles, tools)
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL, -- 'garden', 'kitchen', 'vehicle', 'tool'
    name VARCHAR(255),
    owner_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326),
    capacity JSONB DEFAULT '{}', -- Type-specific capacity info
    availability JSONB DEFAULT '{}', -- Schedule, conditions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Offers (surplus food, capacity, help)
CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES resources(id),
    item_type VARCHAR(100) NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'lbs',
    available_from TIMESTAMPTZ DEFAULT NOW(),
    available_until TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'available', -- 'available', 'matched', 'completed', 'expired'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Needs (programs requiring food, help)
CREATE TABLE needs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID REFERENCES persons(id), -- Programs are stored as persons with type flag
    item_type VARCHAR(100),
    quantity FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'lbs',
    urgency VARCHAR(20) DEFAULT 'normal', -- 'immediate', 'today', 'this_week', 'normal'
    dietary_restrictions TEXT[],
    deadline TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Matches (coordination between offers and needs)
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id UUID REFERENCES offers(id) ON DELETE CASCADE,
    need_id UUID REFERENCES needs(id) ON DELETE CASCADE,
    coordinator_agent_id VARCHAR(100), -- ID of ephemeral coordinator agent
    pickup_location GEOGRAPHY(POINT, 4326),
    delivery_location GEOGRAPHY(POINT, 4326),
    pickup_time TIMESTAMPTZ,
    delivery_time TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'confirmed', 'in_progress', 'completed', 'cancelled'
    participants JSONB DEFAULT '{}', -- volunteer drivers, helpers
    route_info JSONB DEFAULT '{}', -- Mapbox routing data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ======================
-- DIGITAL TWIN SYSTEM
-- ======================

-- Digital Twins (photo-generated conversational entities)
CREATE TABLE digital_twins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'plant', 'person', 'place', 'tool', 'organization'
    entity_subtype VARCHAR(50), -- e.g., 'kalo', 'heiau', 'imu'
    parent_id UUID REFERENCES digital_twins(id), -- Hierarchies (garden contains plants)
    owner_id UUID REFERENCES persons(id), -- Who photographed/created this twin
    photo_hash VARCHAR(64), -- Deduplicate identical photos
    photo_url TEXT, -- Original photo storage
    individuation_data JSONB NOT NULL, -- Extracted unique characteristics
    system_prompt TEXT NOT NULL, -- Generated embodiment instructions
    personality_traits JSONB DEFAULT '{}',
    current_state JSONB DEFAULT '{}', -- Health, condition, phase
    agent_config JSONB DEFAULT '{}', -- Tool access, capabilities
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction TIMESTAMPTZ DEFAULT NOW(),
    interaction_count INTEGER DEFAULT 0
);

-- Twin Memories (episodic, semantic, procedural)
CREATE TABLE twin_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_id UUID REFERENCES digital_twins(id) ON DELETE CASCADE,
    memory_type VARCHAR(20) NOT NULL, -- 'episodic', 'semantic', 'procedural'
    content JSONB NOT NULL,
    embedding VECTOR(1536), -- For semantic search (requires pgvector)
    importance FLOAT DEFAULT 0.5, -- Memory consolidation weight
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    context JSONB DEFAULT '{}'
);

-- Twin Relationships (caretaker, sibling, location, etc.)
CREATE TABLE twin_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_a_id UUID REFERENCES digital_twins(id) ON DELETE CASCADE,
    twin_b_id UUID REFERENCES digital_twins(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'caretaker', 'sibling', 'ingredient', 'location', 'ancestor'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(twin_a_id, twin_b_id, relationship_type)
);

-- Twin Research Cache (avoid re-researching same entities)
CREATE TABLE twin_research_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    query_hash VARCHAR(64) NOT NULL, -- Hash of research query
    research_data JSONB NOT NULL,
    source VARCHAR(50), -- 'web_search', 'mcp', 'database'
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE(entity_type, query_hash)
);

-- ======================
-- AGENT SYSTEM
-- ======================

-- Agent Sessions (track active and historical agent instances)
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL, -- 'person', 'coordinator', 'garden', etc.
    agent_id VARCHAR(100) NOT NULL, -- Unique instance ID
    parent_agent_id VARCHAR(100), -- For hierarchical spawning
    depth INTEGER DEFAULT 0, -- Nesting level
    person_id UUID REFERENCES persons(id),
    digital_twin_id UUID REFERENCES digital_twins(id),
    state JSONB DEFAULT '{}',
    memory JSONB DEFAULT '{}',
    spawned_at TIMESTAMPTZ DEFAULT NOW(),
    retired_at TIMESTAMPTZ,
    lifecycle VARCHAR(20) DEFAULT 'active' -- 'active', 'retired', 'failed'
);

-- Agent Communications (A2A protocol messages)
CREATE TABLE agent_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent_id VARCHAR(100) NOT NULL,
    to_agent_id VARCHAR(100) NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- 'query', 'response', 'handoff', 'coordinate'
    content JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'received', 'processed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- ======================
-- CONVERSATION SYSTEM
-- ======================

-- Voice Sessions (WebRTC conversations)
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES persons(id),
    session_id VARCHAR(255) UNIQUE NOT NULL, -- Hume.ai session ID
    active_agents TEXT[], -- Currently participating agents
    language VARCHAR(10) DEFAULT 'en',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active'
);

-- Conversation Turns (transcriptions, agent responses)
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES voice_sessions(id) ON DELETE CASCADE,
    speaker VARCHAR(100) NOT NULL, -- 'user' or agent_id
    speaker_type VARCHAR(20) NOT NULL, -- 'user', 'person_agent', 'coordinator', etc.
    text TEXT NOT NULL,
    audio_url TEXT, -- Temporary storage, deleted after transcription
    emotions JSONB DEFAULT '{}', -- Hume.ai emotion detection
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_time_ms INTEGER
);

-- ======================
-- COORDINATION PATTERNS
-- ======================

-- Learned Patterns (successful coordination templates)
CREATE TABLE coordination_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL, -- 'offer_need_match', 'volunteer_dispatch', etc.
    context JSONB NOT NULL, -- Conditions when pattern applies
    actions JSONB NOT NULL, -- Steps taken
    success_rate FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================
-- INDEXES
-- ======================

-- Persons
CREATE INDEX idx_persons_phone ON persons(phone);
CREATE INDEX idx_persons_location ON persons USING GIST(location);
CREATE INDEX idx_persons_last_interaction ON persons(last_interaction);

-- Resources
CREATE INDEX idx_resources_type ON resources(type);
CREATE INDEX idx_resources_owner ON resources(owner_id);
CREATE INDEX idx_resources_location ON resources USING GIST(location);

-- Offers & Needs
CREATE INDEX idx_offers_status ON offers(status);
CREATE INDEX idx_offers_item_type ON offers(item_type);
CREATE INDEX idx_offers_available_from ON offers(available_from);
CREATE INDEX idx_needs_status ON needs(status);
CREATE INDEX idx_needs_urgency ON needs(urgency);
CREATE INDEX idx_needs_item_type ON needs(item_type);

-- Matches
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_offer ON matches(offer_id);
CREATE INDEX idx_matches_need ON matches(need_id);

-- Digital Twins
CREATE INDEX idx_twins_type ON digital_twins(entity_type);
CREATE INDEX idx_twins_parent ON digital_twins(parent_id);
CREATE INDEX idx_twins_owner ON digital_twins(owner_id);
CREATE INDEX idx_twins_photo_hash ON digital_twins(photo_hash);
CREATE INDEX idx_twin_memories ON twin_memories(twin_id, memory_type);
CREATE INDEX idx_twin_relationships_a ON twin_relationships(twin_a_id);
CREATE INDEX idx_twin_relationships_b ON twin_relationships(twin_b_id);

-- Agents
CREATE INDEX idx_agent_sessions_type ON agent_sessions(agent_type);
CREATE INDEX idx_agent_sessions_parent ON agent_sessions(parent_agent_id);
CREATE INDEX idx_agent_comms_from ON agent_communications(from_agent_id);
CREATE INDEX idx_agent_comms_to ON agent_communications(to_agent_id);

-- Conversations
CREATE INDEX idx_voice_sessions_person ON voice_sessions(person_id);
CREATE INDEX idx_conversation_turns_session ON conversation_turns(session_id);
CREATE INDEX idx_conversation_turns_timestamp ON conversation_turns(timestamp);

-- ======================
-- FUNCTIONS
-- ======================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_persons_updated_at BEFORE UPDATE ON persons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coordination_patterns_updated_at BEFORE UPDATE ON coordination_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Geographic distance function (km)
CREATE OR REPLACE FUNCTION calculate_distance_km(loc1 GEOGRAPHY, loc2 GEOGRAPHY)
RETURNS FLOAT AS $$
BEGIN
    RETURN ST_Distance(loc1, loc2) / 1000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Find nearby offers
CREATE OR REPLACE FUNCTION find_nearby_offers(
    center_location GEOGRAPHY,
    max_distance_km FLOAT DEFAULT 50.0,
    item_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    offer_id UUID,
    distance_km FLOAT,
    item_type VARCHAR,
    quantity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        calculate_distance_km(center_location, p.location),
        o.item_type,
        o.quantity
    FROM offers o
    JOIN persons p ON o.person_id = p.id
    WHERE
        o.status = 'available'
        AND ST_DWithin(center_location, p.location, max_distance_km * 1000)
        AND (item_filter IS NULL OR o.item_type ILIKE '%' || item_filter || '%')
    ORDER BY calculate_distance_km(center_location, p.location);
END;
$$ LANGUAGE plpgsql;
