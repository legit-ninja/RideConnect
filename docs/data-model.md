
erDiagram
    USER ||--o{ ANIMAL : owns
    USER ||--o{ LISTING : creates
    USER ||--o{ FRIEND_INVITE : sends
    USER ||--o{ FRIEND_INVITE : receives
    USER ||--o{ BOOKING_REQUEST : requests_as_rider
    USER ||--o{ BOOKING_REQUEST : approves_as_owner
    USER ||--o{ VERIFICATION_RECORD : has
    USER ||--o{ REPORT : files
    USER ||--o{ REPORT : is_reported_in
    USER }o--o| USER : guardian_of

    SPECIES ||--o{ ANIMAL : classifies

    ANIMAL ||--o{ LISTING : featured_in

    LISTING ||--o{ BOOKING_REQUEST : generates

    BOOKING_REQUEST ||--o| TRANSACTION : may_have
    BOOKING_REQUEST ||--o{ MESSAGE : contains

    FRIEND_INVITE ||--o{ BOOKING_REQUEST : enables_free_ride

    USER {
        uuid id PK
        string email
        string password_hash
        bool is_rider
        bool is_owner
        bool is_admin
        enum verification_status
        bool is_minor
        uuid guardian_user_id FK
        string phone
        datetime created_at
    }

    VERIFICATION_RECORD {
        uuid id PK
        uuid user_id FK
        string provider
        string provider_reference_id
        enum status
        datetime verified_at
        datetime expires_at
    }

    SPECIES {
        uuid id PK
        string name
        bool active_in_ui
    }

    ANIMAL {
        uuid id PK
        uuid owner_id FK
        uuid species_id FK
        string name
        string breed
        int age
        text description
        float lat
        float lng
        string address
        datetime created_at
    }

    LISTING {
        uuid id PK
        uuid animal_id FK
        uuid owner_id FK
        enum activity_type
        decimal price
        bool friend_only_allowed
        bool active
        datetime created_at
    }

    FRIEND_INVITE {
        uuid id PK
        uuid owner_id FK
        uuid rider_id FK
        enum status
        datetime invited_at
        datetime accepted_at
    }

    BOOKING_REQUEST {
        uuid id PK
        uuid listing_id FK
        uuid rider_id FK
        uuid owner_id FK
        uuid friend_invite_id FK
        enum payment_type
        enum status
        datetime requested_at
        datetime scheduled_at
    }

    TRANSACTION {
        uuid id PK
        uuid booking_request_id FK
        decimal amount
        decimal platform_commission
        string stripe_payment_intent_id
        enum status
        datetime created_at
    }

    MESSAGE {
        uuid id PK
        uuid booking_request_id FK
        uuid sender_id FK
        text body
        datetime sent_at
    }

    REPORT {
        uuid id PK
        uuid reporter_id FK
        uuid reported_user_id FK
        uuid related_booking_id FK
        text reason
        enum status
        datetime created_at
        datetime reviewed_at
    }