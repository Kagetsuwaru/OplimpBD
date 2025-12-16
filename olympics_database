--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5 (Ubuntu 12.5-1.pgdg20.04+1)
-- Dumped by pg_dump version 12.5 (Ubuntu 12.5-1.pgdg20.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_medals_summary(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_medals_summary() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Обновляем существующие записи
    UPDATE country_medals_summary cms
    SET 
        gold_count = sub.gold,
        silver_count = sub.silver,
        bronze_count = sub.bronze,
        last_updated = CURRENT_TIMESTAMP
    FROM (
        SELECT 
            c.country_code,
            COUNT(CASE WHEN r.medal = 'золото' THEN 1 END) as gold,
            COUNT(CASE WHEN r.medal = 'серебро' THEN 1 END) as silver,
            COUNT(CASE WHEN r.medal = 'бронза' THEN 1 END) as bronze
        FROM countries c
        LEFT JOIN participants p ON c.country_code = p.country_code
        LEFT JOIN results r ON p.participant_id = r.participant_id
        GROUP BY c.country_code
    ) sub
    WHERE cms.country_code = sub.country_code;
    
    -- Вставляем новые страны
    INSERT INTO country_medals_summary (country_code, country_name, gold_count, silver_count, bronze_count)
    SELECT 
        c.country_code,
        c.country_name,
        COUNT(CASE WHEN r.medal = 'золото' THEN 1 END),
        COUNT(CASE WHEN r.medal = 'серебро' THEN 1 END),
        COUNT(CASE WHEN r.medal = 'бронза' THEN 1 END)
    FROM countries c
    LEFT JOIN participants p ON c.country_code = p.country_code
    LEFT JOIN results r ON p.participant_id = r.participant_id
    WHERE c.country_code NOT IN (SELECT country_code FROM country_medals_summary)
    GROUP BY c.country_code, c.country_name;
    
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.update_medals_summary() OWNER TO postgres;

--
-- Name: update_schedule_status(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_schedule_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Если добавлены результаты, меняем статус на "завершен"
    UPDATE schedule 
    SET status = 'завершен' 
    WHERE schedule_id = NEW.schedule_id;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_schedule_status() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.participants (
    participant_id integer NOT NULL,
    country_code character(3) NOT NULL,
    sport_code character(5) NOT NULL,
    full_name character varying(200) NOT NULL,
    birth_date date NOT NULL,
    gender character(1),
    height integer,
    weight integer,
    CONSTRAINT participants_gender_check CHECK ((gender = ANY (ARRAY['M'::bpchar, 'F'::bpchar]))),
    CONSTRAINT participants_height_check CHECK (((height >= 100) AND (height <= 250))),
    CONSTRAINT participants_weight_check CHECK (((weight >= 30) AND (weight <= 200)))
);


ALTER TABLE public.participants OWNER TO postgres;

--
-- Name: active_participants; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_participants AS
 SELECT participants.participant_id,
    participants.full_name,
    participants.birth_date,
    date_part('year'::text, age((participants.birth_date)::timestamp with time zone)) AS age
   FROM public.participants
  WHERE (date_part('year'::text, age((participants.birth_date)::timestamp with time zone)) >= (16)::double precision);


ALTER TABLE public.active_participants OWNER TO postgres;

--
-- Name: countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.countries (
    country_code character(3) NOT NULL,
    country_name character varying(100) NOT NULL,
    continent character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT countries_continent_check CHECK (((continent)::text = ANY ((ARRAY['Азия'::character varying, 'Европа'::character varying, 'Африка'::character varying, 'Северная Америка'::character varying, 'Южная Америка'::character varying, 'Австралия'::character varying])::text[])))
);


ALTER TABLE public.countries OWNER TO postgres;

--
-- Name: results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.results (
    result_id integer NOT NULL,
    schedule_id integer NOT NULL,
    participant_id integer NOT NULL,
    "position" integer,
    result_value numeric(10,3),
    medal character varying(10),
    points integer DEFAULT 0,
    CONSTRAINT results_medal_check CHECK (((medal)::text = ANY ((ARRAY['золото'::character varying, 'серебро'::character varying, 'бронза'::character varying, NULL::character varying])::text[]))),
    CONSTRAINT results_position_check CHECK (("position" > 0))
);


ALTER TABLE public.results OWNER TO postgres;

--
-- Name: country_medals; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.country_medals AS
 SELECT c.country_code,
    c.country_name,
    count(
        CASE
            WHEN ((r.medal)::text = 'золото'::text) THEN 1
            ELSE NULL::integer
        END) AS gold_medals,
    count(
        CASE
            WHEN ((r.medal)::text = 'серебро'::text) THEN 1
            ELSE NULL::integer
        END) AS silver_medals,
    count(
        CASE
            WHEN ((r.medal)::text = 'бронза'::text) THEN 1
            ELSE NULL::integer
        END) AS bronze_medals,
    count(r.medal) AS total_medals
   FROM ((public.countries c
     LEFT JOIN public.participants p ON ((c.country_code = p.country_code)))
     LEFT JOIN public.results r ON (((p.participant_id = r.participant_id) AND (r.medal IS NOT NULL))))
  GROUP BY c.country_code, c.country_name
 HAVING (count(r.medal) > 0)
  ORDER BY (count(
        CASE
            WHEN ((r.medal)::text = 'золото'::text) THEN 1
            ELSE NULL::integer
        END)) DESC, (count(
        CASE
            WHEN ((r.medal)::text = 'серебро'::text) THEN 1
            ELSE NULL::integer
        END)) DESC, (count(
        CASE
            WHEN ((r.medal)::text = 'бронза'::text) THEN 1
            ELSE NULL::integer
        END)) DESC;


ALTER TABLE public.country_medals OWNER TO postgres;

--
-- Name: country_medals_summary; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.country_medals_summary (
    country_code character(3) NOT NULL,
    country_name character varying(100),
    gold_count integer DEFAULT 0,
    silver_count integer DEFAULT 0,
    bronze_count integer DEFAULT 0,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.country_medals_summary OWNER TO postgres;

--
-- Name: schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schedule (
    schedule_id integer NOT NULL,
    sport_code character(5) NOT NULL,
    venue_code character(5) NOT NULL,
    start_date date NOT NULL,
    start_time time without time zone NOT NULL,
    stage character varying(50),
    status character varying(20) DEFAULT 'запланирован'::character varying,
    CONSTRAINT schedule_stage_check CHECK (((stage)::text = ANY ((ARRAY['квалификация'::character varying, '1/8 финала'::character varying, '1/4 финала'::character varying, 'полуфинал'::character varying, 'финал'::character varying])::text[]))),
    CONSTRAINT schedule_status_check CHECK (((status)::text = ANY ((ARRAY['запланирован'::character varying, 'идет'::character varying, 'завершен'::character varying, 'отменен'::character varying])::text[])))
);


ALTER TABLE public.schedule OWNER TO postgres;

--
-- Name: sports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sports (
    sport_code character(5) NOT NULL,
    sport_name character varying(100) NOT NULL,
    is_team boolean NOT NULL,
    description text,
    max_participants integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT sports_max_participants_check CHECK ((max_participants > 0))
);


ALTER TABLE public.sports OWNER TO postgres;

--
-- Name: venues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.venues (
    venue_code character(5) NOT NULL,
    venue_name character varying(200) NOT NULL,
    location character varying(200) NOT NULL,
    capacity integer,
    venue_type character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT venues_capacity_check CHECK ((capacity > 0)),
    CONSTRAINT venues_venue_type_check CHECK (((venue_type)::text = ANY ((ARRAY['стадион'::character varying, 'бассейн'::character varying, 'зал'::character varying, 'трасса'::character varying, 'поле'::character varying, 'корт'::character varying])::text[])))
);


ALTER TABLE public.venues OWNER TO postgres;

--
-- Name: daily_schedule; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.daily_schedule AS
 SELECT s.start_date,
    s.start_time,
    v.venue_name,
    v.location,
    sp.sport_name,
    s.stage,
    s.status,
    count(DISTINCT r.participant_id) AS participants_count
   FROM (((public.schedule s
     JOIN public.venues v ON ((s.venue_code = v.venue_code)))
     JOIN public.sports sp ON ((s.sport_code = sp.sport_code)))
     LEFT JOIN public.results r ON ((s.schedule_id = r.schedule_id)))
  GROUP BY s.schedule_id, s.start_date, s.start_time, v.venue_name, v.location, sp.sport_name, s.stage, s.status;


ALTER TABLE public.daily_schedule OWNER TO postgres;

--
-- Name: participants_details; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.participants_details AS
 SELECT p.participant_id,
    p.full_name,
    p.birth_date,
    date_part('year'::text, age((p.birth_date)::timestamp with time zone)) AS age,
    p.gender,
    c.country_name,
    s.sport_name,
    s.is_team
   FROM ((public.participants p
     JOIN public.countries c ON ((p.country_code = c.country_code)))
     JOIN public.sports s ON ((p.sport_code = s.sport_code)));


ALTER TABLE public.participants_details OWNER TO postgres;

--
-- Name: participants_participant_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.participants_participant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.participants_participant_id_seq OWNER TO postgres;

--
-- Name: participants_participant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.participants_participant_id_seq OWNED BY public.participants.participant_id;


--
-- Name: results_result_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.results_result_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.results_result_id_seq OWNER TO postgres;

--
-- Name: results_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.results_result_id_seq OWNED BY public.results.result_id;


--
-- Name: schedule_schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schedule_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schedule_schedule_id_seq OWNER TO postgres;

--
-- Name: schedule_schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schedule_schedule_id_seq OWNED BY public.schedule.schedule_id;


--
-- Name: participants participant_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants ALTER COLUMN participant_id SET DEFAULT nextval('public.participants_participant_id_seq'::regclass);


--
-- Name: results result_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.results ALTER COLUMN result_id SET DEFAULT nextval('public.results_result_id_seq'::regclass);


--
-- Name: schedule schedule_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule ALTER COLUMN schedule_id SET DEFAULT nextval('public.schedule_schedule_id_seq'::regclass);


--
-- Data for Name: countries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.countries (country_code, country_name, continent, created_at) FROM stdin;
RUS	Россия	Европа	2025-10-23 09:03:29.657096
USA	США	Северная Америка	2025-10-23 09:03:29.657096
CHN	Китай	Азия	2025-10-23 09:03:29.657096
GER	Германия	Европа	2025-10-23 09:03:29.657096
JPN	Япония	Азия	2025-10-23 09:03:29.657096
FRA	Франция	Европа	2025-10-23 09:03:29.657096
GBR	Великобритания	Европа	2025-10-23 09:03:29.657096
AUS	Австралия	Австралия	2025-10-23 09:03:29.657096
BRA	Бразилия	Южная Америка	2025-10-23 09:03:29.657096
ITA	Италия	Европа	2025-10-23 09:03:29.657096
\.


--
-- Data for Name: country_medals_summary; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.country_medals_summary (country_code, country_name, gold_count, silver_count, bronze_count, last_updated) FROM stdin;
GBR	Великобритания	0	0	0	2025-12-11 10:12:26.60177
USA	США	1	0	0	2025-12-11 10:12:26.60177
RUS	Россия	0	2	0	2025-12-11 10:12:26.60177
GER	Германия	0	0	1	2025-12-11 10:12:26.60177
AUS	Австралия	0	0	0	2025-12-11 10:12:26.60177
FRA	Франция	0	0	0	2025-12-11 10:12:26.60177
CHN	Китай	1	0	0	2025-12-11 10:12:26.60177
BRA	Бразилия	0	0	0	2025-12-11 10:12:26.60177
ITA	Италия	0	0	0	2025-12-11 10:12:26.60177
JPN	Япония	0	0	1	2025-12-11 10:12:26.60177
\.


--
-- Data for Name: participants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.participants (participant_id, country_code, sport_code, full_name, birth_date, gender, height, weight) FROM stdin;
1	RUS	SWIM 	Иванов Александр Сергеевич	1998-03-15	M	185	78
2	RUS	SWIM 	Петрова Мария Владимировна	2000-07-22	F	172	62
3	RUS	GYM  	Сидоров Дмитрий Игоревич	1997-11-30	M	170	65
4	RUS	GYM  	Козлова Анна Петровна	2001-05-14	F	162	48
5	RUS	BASK 	Смирнов Алексей Николаевич	1995-08-10	M	205	95
6	RUS	BASK 	Волков Павел Олегович	1996-12-03	M	198	92
7	RUS	ATHL 	Николаева Елена Викторовна	1999-02-18	F	168	55
8	RUS	FENC 	Орлов Михаил Александрович	1994-09-25	M	180	75
9	USA	SWIM 	Michael Phelps	1990-06-30	M	193	88
10	USA	SWIM 	Katie Ledecky	1997-03-17	F	183	68
11	USA	BASK 	LeBron James	1984-12-30	M	206	113
12	USA	BASK 	Stephen Curry	1988-03-14	M	188	86
13	USA	ATHL 	Allyson Felix	1985-11-18	F	168	57
14	USA	TENN 	Serena Williams	1981-09-26	F	175	72
15	CHN	GYM  	Zhang Wei	1999-04-12	M	165	58
16	CHN	GYM  	Li Na	2002-01-08	F	155	42
17	CHN	DIVE 	Wang Li	1998-08-19	F	160	50
18	CHN	WEIG 	Chen Long	1993-11-25	M	175	105
19	GER	CYCL 	Thomas Müller	1992-03-13	M	182	74
20	GER	FENC 	Anna Schmidt	1996-07-07	F	170	60
21	GER	ROW  	Hans Bauer	1994-12-20	M	195	90
22	JPN	GYM  	Tanaka Hiroshi	2000-06-15	M	168	62
23	JPN	SWIM 	Yamamoto Yuki	1999-09-08	F	165	55
24	JPN	TENN 	Nishikori Kei	1989-12-29	M	178	75
25	FRA	FENC 	Pierre Dubois	1995-02-14	M	185	80
26	GBR	ATHL 	Emma Watson	1997-04-15	F	170	58
27	AUS	SWIM 	James Wilson	1998-11-23	M	190	82
28	BRA	BASK 	Carlos Silva	1996-07-30	M	200	98
29	ITA	FENC 	Giuseppe Rossi	1993-05-10	M	178	72
30	ITA	SWIM 	Marco Pollos	1993-12-17	M	177	78
\.


--
-- Data for Name: results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.results (result_id, schedule_id, participant_id, "position", result_value, medal, points) FROM stdin;
27	3	1	2	48.520	серебро	2
28	3	9	1	47.890	золото	3
29	3	19	3	48.780	бронза	1
30	2	1	1	48.450	\N	0
31	2	9	2	48.120	\N	0
32	2	19	3	48.900	\N	0
33	5	3	1	85.650	\N	0
34	5	4	2	84.320	\N	0
35	5	16	3	83.980	\N	0
36	5	17	4	83.450	\N	0
37	7	5	1	\N	\N	0
38	7	6	1	\N	\N	0
39	7	11	2	\N	\N	0
40	7	12	2	\N	\N	0
41	10	7	1	10.850	\N	0
42	10	14	2	10.920	\N	0
43	10	26	3	11.050	\N	0
44	13	8	1	\N	\N	0
45	13	20	2	\N	\N	0
46	13	27	3	\N	\N	0
47	13	29	4	\N	\N	0
48	17	23	1	\N	\N	0
49	17	15	2	\N	\N	0
50	20	18	1	385.500	золото	3
51	20	3	2	380.000	серебро	2
52	20	24	3	375.500	бронза	1
\.


--
-- Data for Name: schedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.schedule (schedule_id, sport_code, venue_code, start_date, start_time, stage, status) FROM stdin;
1	SWIM 	POOL 	2024-07-25	10:00:00	квалификация	завершен
4	SWIM 	POOL 	2024-07-27	10:00:00	квалификация	запланирован
6	GYM  	GYM1 	2024-07-27	15:00:00	финал	запланирован
8	BASK 	CTR1 	2024-07-26	16:00:00	1/4 финала	завершен
9	BASK 	CTR1 	2024-07-27	20:00:00	полуфинал	запланирован
11	ATHL 	STD1 	2024-07-26	09:00:00	квалификация	завершен
12	ATHL 	STD1 	2024-07-27	18:00:00	финал	запланирован
14	FENC 	FENC 	2024-07-26	14:30:00	1/4 финала	завершен
15	FENC 	FENC 	2024-07-27	16:00:00	полуфинал	запланирован
16	FENC 	FENC 	2024-07-28	17:00:00	финал	запланирован
18	TENN 	TENN 	2024-07-27	14:00:00	полуфинал	запланирован
19	DIVE 	DIVE 	2024-07-27	11:00:00	квалификация	запланирован
21	WEIG 	WEIG 	2024-07-26	15:00:00	финал	завершен
22	ROW  	ROW  	2024-07-27	08:00:00	финал	запланирован
3	SWIM 	POOL 	2024-07-26	19:00:00	финал	завершен
2	SWIM 	POOL 	2024-07-25	18:30:00	полуфинал	завершен
5	GYM  	GYM1 	2024-07-26	11:00:00	квалификация	завершен
7	BASK 	CTR1 	2024-07-25	14:00:00	1/8 финала	завершен
10	BASK 	CTR1 	2024-07-28	21:00:00	финал	завершен
13	FENC 	FENC 	2024-07-25	13:00:00	1/8 финала	завершен
17	TENN 	TENN 	2024-07-26	12:00:00	1/4 финала	завершен
20	CYCL 	CYCL 	2024-07-28	10:00:00	финал	завершен
\.


--
-- Data for Name: sports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sports (sport_code, sport_name, is_team, description, max_participants, created_at) FROM stdin;
SWIM 	Плавание	f	Соревнования в бассейне на различные дистанции	8	2025-10-23 09:06:00.633127
GYM  	Гимнастика	f	Спортивная гимнастика на различных снарядах	10	2025-10-23 09:06:00.633127
BASK 	Баскетбол	t	Командная игра с мячом	12	2025-10-23 09:06:00.633127
ATHL 	Легкая атлетика	f	Беговые и технические дисциплины	8	2025-10-23 09:06:00.633127
FENC 	Фехтование	f	Соревнования на рапирах, шпагах, саблях	2	2025-10-23 09:06:00.633127
TENN 	Теннис	f	Одиночные и парные соревнования	2	2025-10-23 09:06:00.633127
DIVE 	Прыжки в воду	f	Прыжки с трамплина и вышки	6	2025-10-23 09:06:00.633127
CYCL 	Велоспорт	f	Трековые и шоссейные гонки	15	2025-10-23 09:06:00.633127
WEIG 	Тяжелая атлетика	f	Соревнования по поднятию штанги	10	2025-10-23 09:06:00.633127
ROW  	Академическая гребля	t	Командные гонки на байдарках и каноэ	4	2025-10-23 09:06:00.633127
\.


--
-- Data for Name: venues; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.venues (venue_code, venue_name, location, capacity, venue_type, created_at) FROM stdin;
STD1 	Олимпийский стадион	Олимпийский парк, зона А	80000	стадион	2025-10-23 09:06:07.66144
POOL 	Водный дворец	Олимпийский парк, зона Б	15000	бассейн	2025-10-23 09:06:07.66144
GYM1 	Гимнастический зал	Олимпийский парк, зона В	12000	зал	2025-10-23 09:06:07.66144
CTR1 	Баскетбольный центр	Олимпийский парк, зона Г	18000	зал	2025-10-23 09:06:07.66144
FENC 	Фехтовальный центр	Олимпийский парк, зона Д	8000	зал	2025-10-23 09:06:07.66144
TENN 	Теннисный центр	Олимпийский парк, зона Е	14000	корт	2025-10-23 09:06:07.66144
DIVE 	Центр прыжков в воду	Олимпийский парк, зона Ж	10000	бассейн	2025-10-23 09:06:07.66144
CYCL 	Велотрек	Олимпийский парк, зона З	6000	трасса	2025-10-23 09:06:07.66144
WEIG 	Тяжелоатлетический зал	Олимпийский парк, зона И	9000	зал	2025-10-23 09:06:07.66144
ROW  	Гребной канал	Олимпийский парк, зона К	20000	трасса	2025-10-23 09:06:07.66144
\.


--
-- Name: participants_participant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.participants_participant_id_seq', 31, true);


--
-- Name: results_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.results_result_id_seq', 52, true);


--
-- Name: schedule_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.schedule_schedule_id_seq', 22, true);


--
-- Name: countries countries_country_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_country_name_key UNIQUE (country_name);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (country_code);


--
-- Name: country_medals_summary country_medals_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country_medals_summary
    ADD CONSTRAINT country_medals_summary_pkey PRIMARY KEY (country_code);


--
-- Name: participants participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT participants_pkey PRIMARY KEY (participant_id);


--
-- Name: results results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (result_id);


--
-- Name: schedule schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_pkey PRIMARY KEY (schedule_id);


--
-- Name: sports sports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sports
    ADD CONSTRAINT sports_pkey PRIMARY KEY (sport_code);


--
-- Name: sports sports_sport_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sports
    ADD CONSTRAINT sports_sport_name_key UNIQUE (sport_name);


--
-- Name: results unique_participant_per_race; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT unique_participant_per_race UNIQUE (schedule_id, participant_id);


--
-- Name: venues venues_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.venues
    ADD CONSTRAINT venues_pkey PRIMARY KEY (venue_code);


--
-- Name: idx_participants_birth_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_participants_birth_date ON public.participants USING btree (birth_date);


--
-- Name: idx_participants_country; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_participants_country ON public.participants USING btree (country_code);


--
-- Name: idx_participants_country_sport; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_participants_country_sport ON public.participants USING btree (country_code, sport_code);


--
-- Name: idx_participants_sport; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_participants_sport ON public.participants USING btree (sport_code);


--
-- Name: idx_results_medal; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_results_medal ON public.results USING btree (medal);


--
-- Name: idx_results_position; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_results_position ON public.results USING btree ("position");


--
-- Name: idx_results_schedule; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_results_schedule ON public.results USING btree (schedule_id);


--
-- Name: idx_schedule_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_schedule_date ON public.schedule USING btree (start_date);


--
-- Name: idx_schedule_date_sport; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_schedule_date_sport ON public.schedule USING btree (start_date, sport_code);


--
-- Name: idx_schedule_sport; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_schedule_sport ON public.schedule USING btree (sport_code);


--
-- Name: results trg_update_medals_summary; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_medals_summary AFTER INSERT OR DELETE OR UPDATE ON public.results FOR EACH STATEMENT EXECUTE FUNCTION public.update_medals_summary();


--
-- Name: results trg_update_schedule_status; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_schedule_status AFTER INSERT ON public.results FOR EACH ROW EXECUTE FUNCTION public.update_schedule_status();


--
-- Name: participants fk_participant_country; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT fk_participant_country FOREIGN KEY (country_code) REFERENCES public.countries(country_code) ON DELETE CASCADE;


--
-- Name: participants fk_participant_sport; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT fk_participant_sport FOREIGN KEY (sport_code) REFERENCES public.sports(sport_code) ON DELETE CASCADE;


--
-- Name: results fk_result_participant; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT fk_result_participant FOREIGN KEY (participant_id) REFERENCES public.participants(participant_id) ON DELETE CASCADE;


--
-- Name: results fk_result_schedule; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT fk_result_schedule FOREIGN KEY (schedule_id) REFERENCES public.schedule(schedule_id) ON DELETE CASCADE;


--
-- Name: schedule fk_schedule_sport; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT fk_schedule_sport FOREIGN KEY (sport_code) REFERENCES public.sports(sport_code) ON DELETE CASCADE;


--
-- Name: schedule fk_schedule_venue; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT fk_schedule_venue FOREIGN KEY (venue_code) REFERENCES public.venues(venue_code) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--
