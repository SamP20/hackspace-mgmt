CREATE TYPE public.legacy_machine_auth AS ENUM
    ('none', 'password', 'padlock');

ALTER TABLE IF EXISTS public.machine
    ADD COLUMN legacy_auth legacy_machine_auth NOT NULL DEFAULT 'none'::legacy_machine_auth;

ALTER TABLE IF EXISTS public.machine
    ADD COLUMN legacy_password character varying(255) NOT NULL DEFAULT '';

ALTER TABLE IF EXISTS public.induction
    ADD UNIQUE (machine_id, member_id);