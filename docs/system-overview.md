---
title: OTT Platform PoC — System Overview
---
```Mermaid
graph TB
    subgraph FE["Frontend (React)"]
        Home["Home<br/><small>Catch-Up Rail</small>"]
        EPG["EPG<br/><small>Catch-Up Badges</small>"]
        Player["Player<br/><small>hls.js + EME</small>"]
        Upsell["Upsell<br/><small>Prompts</small>"]
        AdminUI["Admin Dashboard<br/><small>Subscriber · Streaming · DRM</small>"]
        PVR_UI["My Recordings<br/><small>(future)</small>"]:::future
    end

    subgraph BE["Backend (FastAPI)"]
        subgraph BE_Core["Core Services"]
            Auth["Auth<br/><small>JWT</small>"]
            TSTV["TSTV Router<br/><small>Start-Over + Catch-Up<br/>Manifest Generation</small>"]
            DRM["DRM License<br/><small>ClearKey / CENC</small>"]
            Entitle["Entitlement<br/>Service"]:::critical
            Subs["Subscription<br/>Mgmt"]
            KeyMgmt["Key Mgmt<br/><small>AES-128 per channel</small>"]
        end
        subgraph BE_Admin["Admin & Operations"]
            SimMgr["SimLive<br/>Manager<br/><small>start/stop/status</small>"]
            AdminAPI["Admin API<br/><small>CRUD</small>"]
            Diag["Diagnostic<br/>Tool<br/><small>Why can't I watch X?</small>"]
            Schedule["Schedule<br/>EPG Data"]
            Sessions["Session<br/>Analytics"]
            PVR_Sched["PVR<br/>Scheduler"]:::future
        end
    end

    subgraph STREAM["Streaming Infrastructure (Docker)"]
        SimLive["SimLive<br/><small>FFmpeg × N channels<br/>HLS fMP4 + CENC + drawtext</small>"]
        CDN["CDN<br/><small>nginx direct serve<br/>7-day retention</small>"]
        HLS[("hls_data volume<br/><small>Encrypted fMP4 segments<br/>strftime filenames</small>")]
    end

    subgraph DATA["Data Layer"]
        PG[("PostgreSQL")]
        Tables["users · channels · schedule_entries<br/>products · product_entitlements · user_subscriptions<br/>drm_keys · tstv_sessions · recordings · series_links"]
    end

    %% Frontend → Backend
    EPG -->|"catch-up / start-over"| TSTV
    Player -->|"license request<br/>(JWT + KID)"| DRM
    Player -->|"HLS segments"| CDN
    AdminUI --> AdminAPI
    Home --> TSTV
    Upsell --> Subs
    PVR_UI -.-> PVR_Sched

    %% Backend internal — Entitlement is the policy engine
    DRM -->|"checks"| Entitle
    TSTV -->|"checks"| Entitle
    Entitle --- Subs
    Diag -->|"resolves"| Entitle
    DRM --- KeyMgmt

    %% Backend → Streaming
    SimMgr -->|"start / stop<br/>FFmpeg processes"| SimLive
    KeyMgmt -->|"encryption keys<br/>(key_id + key_hex)"| SimLive

    %% Backend → Data
    TSTV -->|"reads segments"| HLS
    BE_Core --> PG
    BE_Admin --> PG
    PG --- Tables

    %% Streaming internal
    SimLive -->|"writes"| HLS
    CDN -->|"serves from"| HLS

    %% Styling
    classDef future stroke-dasharray: 5 5,stroke:#8b5cf6,fill:#f3f0ff
    classDef critical fill:#ffc9c9,stroke:#ef4444,stroke-width:2px

    style FE fill:#dbe4ff,stroke:#4a9eed,stroke-width:1px
    style BE fill:#e5dbff,stroke:#8b5cf6,stroke-width:1px
    style BE_Core fill:#e5dbff,stroke:#8b5cf6,stroke-width:1px,stroke-dasharray:0
    style BE_Admin fill:#e5dbff,stroke:#8b5cf6,stroke-width:1px,stroke-dasharray:0
    style STREAM fill:#d3f9d8,stroke:#22c55e,stroke-width:1px
    style DATA fill:#fff3bf,stroke:#f59e0b,stroke-width:1px
```