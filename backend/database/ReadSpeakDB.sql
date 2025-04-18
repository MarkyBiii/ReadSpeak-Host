PGDMP  '                 	    |            ReadSpeakDB    17.0    17.0 8    )           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            *           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            +           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            ,           1262    16384    ReadSpeakDB    DATABASE     �   CREATE DATABASE "ReadSpeakDB" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.932';
    DROP DATABASE "ReadSpeakDB";
                     postgres    false            �            1259    16464    alembic_version    TABLE     X   CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
 #   DROP TABLE public.alembic_version;
       public         heap r       postgres    false            �            1259    16467    assessment_history    TABLE       CREATE TABLE public.assessment_history (
    history_id integer NOT NULL,
    student_id integer,
    assessment_id integer,
    phoneme_output character varying[],
    score double precision,
    date_taken timestamp without time zone,
    audio_url character varying
);
 &   DROP TABLE public.assessment_history;
       public         heap r       postgres    false            �            1259    16472 !   assessment_history_history_id_seq    SEQUENCE     �   CREATE SEQUENCE public.assessment_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 8   DROP SEQUENCE public.assessment_history_history_id_seq;
       public               postgres    false    218            -           0    0 !   assessment_history_history_id_seq    SEQUENCE OWNED BY     g   ALTER SEQUENCE public.assessment_history_history_id_seq OWNED BY public.assessment_history.history_id;
          public               postgres    false    219            �            1259    16473    pronunciation_assessment_types    TABLE     v   CREATE TABLE public.pronunciation_assessment_types (
    type_id integer NOT NULL,
    type_name character varying
);
 2   DROP TABLE public.pronunciation_assessment_types;
       public         heap r       postgres    false            �            1259    16478 *   pronunciation_assessment_types_type_id_seq    SEQUENCE     �   CREATE SEQUENCE public.pronunciation_assessment_types_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 A   DROP SEQUENCE public.pronunciation_assessment_types_type_id_seq;
       public               postgres    false    220            .           0    0 *   pronunciation_assessment_types_type_id_seq    SEQUENCE OWNED BY     y   ALTER SEQUENCE public.pronunciation_assessment_types_type_id_seq OWNED BY public.pronunciation_assessment_types.type_id;
          public               postgres    false    221            �            1259    16479    pronunciation_assessments    TABLE     �   CREATE TABLE public.pronunciation_assessments (
    assessment_id integer NOT NULL,
    text_content character varying,
    phoneme_content character varying[],
    teacher_id integer,
    assessment_type integer
);
 -   DROP TABLE public.pronunciation_assessments;
       public         heap r       postgres    false            �            1259    16484 +   pronunciation_assessments_assessment_id_seq    SEQUENCE     �   CREATE SEQUENCE public.pronunciation_assessments_assessment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 B   DROP SEQUENCE public.pronunciation_assessments_assessment_id_seq;
       public               postgres    false    222            /           0    0 +   pronunciation_assessments_assessment_id_seq    SEQUENCE OWNED BY     {   ALTER SEQUENCE public.pronunciation_assessments_assessment_id_seq OWNED BY public.pronunciation_assessments.assessment_id;
          public               postgres    false    223            �            1259    16485    users    TABLE     .  CREATE TABLE public.users (
    user_id integer NOT NULL,
    name character varying,
    email character varying,
    role character varying,
    hashed_password character varying,
    date_created timestamp without time zone,
    is_verified boolean,
    date_verified timestamp without time zone
);
    DROP TABLE public.users;
       public         heap r       postgres    false            �            1259    16490    users_user_id_seq    SEQUENCE     �   CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.users_user_id_seq;
       public               postgres    false    224            0           0    0    users_user_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;
          public               postgres    false    225            j           2604    16491    assessment_history history_id    DEFAULT     �   ALTER TABLE ONLY public.assessment_history ALTER COLUMN history_id SET DEFAULT nextval('public.assessment_history_history_id_seq'::regclass);
 L   ALTER TABLE public.assessment_history ALTER COLUMN history_id DROP DEFAULT;
       public               postgres    false    219    218            k           2604    16492 &   pronunciation_assessment_types type_id    DEFAULT     �   ALTER TABLE ONLY public.pronunciation_assessment_types ALTER COLUMN type_id SET DEFAULT nextval('public.pronunciation_assessment_types_type_id_seq'::regclass);
 U   ALTER TABLE public.pronunciation_assessment_types ALTER COLUMN type_id DROP DEFAULT;
       public               postgres    false    221    220            l           2604    16493 '   pronunciation_assessments assessment_id    DEFAULT     �   ALTER TABLE ONLY public.pronunciation_assessments ALTER COLUMN assessment_id SET DEFAULT nextval('public.pronunciation_assessments_assessment_id_seq'::regclass);
 V   ALTER TABLE public.pronunciation_assessments ALTER COLUMN assessment_id DROP DEFAULT;
       public               postgres    false    223    222            m           2604    16494    users user_id    DEFAULT     n   ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);
 <   ALTER TABLE public.users ALTER COLUMN user_id DROP DEFAULT;
       public               postgres    false    225    224                      0    16464    alembic_version 
   TABLE DATA           6   COPY public.alembic_version (version_num) FROM stdin;
    public               postgres    false    217   H                 0    16467    assessment_history 
   TABLE DATA           �   COPY public.assessment_history (history_id, student_id, assessment_id, phoneme_output, score, date_taken, audio_url) FROM stdin;
    public               postgres    false    218   9H       !          0    16473    pronunciation_assessment_types 
   TABLE DATA           L   COPY public.pronunciation_assessment_types (type_id, type_name) FROM stdin;
    public               postgres    false    220   3I       #          0    16479    pronunciation_assessments 
   TABLE DATA           ~   COPY public.pronunciation_assessments (assessment_id, text_content, phoneme_content, teacher_id, assessment_type) FROM stdin;
    public               postgres    false    222   bI       %          0    16485    users 
   TABLE DATA           v   COPY public.users (user_id, name, email, role, hashed_password, date_created, is_verified, date_verified) FROM stdin;
    public               postgres    false    224   �I       1           0    0 !   assessment_history_history_id_seq    SEQUENCE SET     O   SELECT pg_catalog.setval('public.assessment_history_history_id_seq', 3, true);
          public               postgres    false    219            2           0    0 *   pronunciation_assessment_types_type_id_seq    SEQUENCE SET     Y   SELECT pg_catalog.setval('public.pronunciation_assessment_types_type_id_seq', 1, false);
          public               postgres    false    221            3           0    0 +   pronunciation_assessments_assessment_id_seq    SEQUENCE SET     Y   SELECT pg_catalog.setval('public.pronunciation_assessments_assessment_id_seq', 3, true);
          public               postgres    false    223            4           0    0    users_user_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.users_user_id_seq', 3, true);
          public               postgres    false    225            o           2606    16496 #   alembic_version alembic_version_pkc 
   CONSTRAINT     j   ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
 M   ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
       public                 postgres    false    217            q           2606    16498 *   assessment_history assessment_history_pkey 
   CONSTRAINT     p   ALTER TABLE ONLY public.assessment_history
    ADD CONSTRAINT assessment_history_pkey PRIMARY KEY (history_id);
 T   ALTER TABLE ONLY public.assessment_history DROP CONSTRAINT assessment_history_pkey;
       public                 postgres    false    218            z           2606    16500 B   pronunciation_assessment_types pronunciation_assessment_types_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.pronunciation_assessment_types
    ADD CONSTRAINT pronunciation_assessment_types_pkey PRIMARY KEY (type_id);
 l   ALTER TABLE ONLY public.pronunciation_assessment_types DROP CONSTRAINT pronunciation_assessment_types_pkey;
       public                 postgres    false    220                       2606    16502 8   pronunciation_assessments pronunciation_assessments_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.pronunciation_assessments
    ADD CONSTRAINT pronunciation_assessments_pkey PRIMARY KEY (assessment_id);
 b   ALTER TABLE ONLY public.pronunciation_assessments DROP CONSTRAINT pronunciation_assessments_pkey;
       public                 postgres    false    222            �           2606    16504    users users_pkey 
   CONSTRAINT     S   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public                 postgres    false    224            r           1259    16539    ix_assessment_history_audio_url    INDEX     c   CREATE INDEX ix_assessment_history_audio_url ON public.assessment_history USING btree (audio_url);
 3   DROP INDEX public.ix_assessment_history_audio_url;
       public                 postgres    false    218            s           1259    16505     ix_assessment_history_date_taken    INDEX     e   CREATE INDEX ix_assessment_history_date_taken ON public.assessment_history USING btree (date_taken);
 4   DROP INDEX public.ix_assessment_history_date_taken;
       public                 postgres    false    218            t           1259    16506     ix_assessment_history_history_id    INDEX     e   CREATE INDEX ix_assessment_history_history_id ON public.assessment_history USING btree (history_id);
 4   DROP INDEX public.ix_assessment_history_history_id;
       public                 postgres    false    218            u           1259    16507 $   ix_assessment_history_phoneme_output    INDEX     m   CREATE INDEX ix_assessment_history_phoneme_output ON public.assessment_history USING btree (phoneme_output);
 8   DROP INDEX public.ix_assessment_history_phoneme_output;
       public                 postgres    false    218            v           1259    16508    ix_assessment_history_score    INDEX     [   CREATE INDEX ix_assessment_history_score ON public.assessment_history USING btree (score);
 /   DROP INDEX public.ix_assessment_history_score;
       public                 postgres    false    218            w           1259    16509 )   ix_pronunciation_assessment_types_type_id    INDEX     w   CREATE INDEX ix_pronunciation_assessment_types_type_id ON public.pronunciation_assessment_types USING btree (type_id);
 =   DROP INDEX public.ix_pronunciation_assessment_types_type_id;
       public                 postgres    false    220            x           1259    16510 +   ix_pronunciation_assessment_types_type_name    INDEX     {   CREATE INDEX ix_pronunciation_assessment_types_type_name ON public.pronunciation_assessment_types USING btree (type_name);
 ?   DROP INDEX public.ix_pronunciation_assessment_types_type_name;
       public                 postgres    false    220            {           1259    16511 *   ix_pronunciation_assessments_assessment_id    INDEX     y   CREATE INDEX ix_pronunciation_assessments_assessment_id ON public.pronunciation_assessments USING btree (assessment_id);
 >   DROP INDEX public.ix_pronunciation_assessments_assessment_id;
       public                 postgres    false    222            |           1259    16512 ,   ix_pronunciation_assessments_phoneme_content    INDEX     }   CREATE INDEX ix_pronunciation_assessments_phoneme_content ON public.pronunciation_assessments USING btree (phoneme_content);
 @   DROP INDEX public.ix_pronunciation_assessments_phoneme_content;
       public                 postgres    false    222            }           1259    16513 )   ix_pronunciation_assessments_text_content    INDEX     w   CREATE INDEX ix_pronunciation_assessments_text_content ON public.pronunciation_assessments USING btree (text_content);
 =   DROP INDEX public.ix_pronunciation_assessments_text_content;
       public                 postgres    false    222            �           1259    16540    ix_users_date_created    INDEX     O   CREATE INDEX ix_users_date_created ON public.users USING btree (date_created);
 )   DROP INDEX public.ix_users_date_created;
       public                 postgres    false    224            �           1259    16541    ix_users_date_verified    INDEX     Q   CREATE INDEX ix_users_date_verified ON public.users USING btree (date_verified);
 *   DROP INDEX public.ix_users_date_verified;
       public                 postgres    false    224            �           1259    16515    ix_users_email    INDEX     A   CREATE INDEX ix_users_email ON public.users USING btree (email);
 "   DROP INDEX public.ix_users_email;
       public                 postgres    false    224            �           1259    16542    ix_users_is_verified    INDEX     M   CREATE INDEX ix_users_is_verified ON public.users USING btree (is_verified);
 (   DROP INDEX public.ix_users_is_verified;
       public                 postgres    false    224            �           1259    16516    ix_users_name    INDEX     ?   CREATE INDEX ix_users_name ON public.users USING btree (name);
 !   DROP INDEX public.ix_users_name;
       public                 postgres    false    224            �           1259    16517    ix_users_role    INDEX     ?   CREATE INDEX ix_users_role ON public.users USING btree (role);
 !   DROP INDEX public.ix_users_role;
       public                 postgres    false    224            �           1259    16518    ix_users_user_id    INDEX     E   CREATE INDEX ix_users_user_id ON public.users USING btree (user_id);
 $   DROP INDEX public.ix_users_user_id;
       public                 postgres    false    224            �           2606    16519 8   assessment_history assessment_history_assessment_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.assessment_history
    ADD CONSTRAINT assessment_history_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.pronunciation_assessments(assessment_id);
 b   ALTER TABLE ONLY public.assessment_history DROP CONSTRAINT assessment_history_assessment_id_fkey;
       public               postgres    false    222    218    4735            �           2606    16524 5   assessment_history assessment_history_student_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.assessment_history
    ADD CONSTRAINT assessment_history_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(user_id);
 _   ALTER TABLE ONLY public.assessment_history DROP CONSTRAINT assessment_history_student_id_fkey;
       public               postgres    false    218    224    4744            �           2606    16529 H   pronunciation_assessments pronunciation_assessments_assessment_type_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pronunciation_assessments
    ADD CONSTRAINT pronunciation_assessments_assessment_type_fkey FOREIGN KEY (assessment_type) REFERENCES public.pronunciation_assessment_types(type_id);
 r   ALTER TABLE ONLY public.pronunciation_assessments DROP CONSTRAINT pronunciation_assessments_assessment_type_fkey;
       public               postgres    false    4730    220    222            �           2606    16534 C   pronunciation_assessments pronunciation_assessments_teacher_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pronunciation_assessments
    ADD CONSTRAINT pronunciation_assessments_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.users(user_id);
 m   ALTER TABLE ONLY public.pronunciation_assessments DROP CONSTRAINT pronunciation_assessments_teacher_id_fkey;
       public               postgres    false    224    4744    222                  x�K1N40K1LII�L����� 0�l         �   x�m�1N�0�g��k��׉�	���R�:�j҄1ucf��+3�s*�����'}� Hynh�PO�^�]�H�9m�B A�|.`.�L�FJ#K�A��dy��"^|H���_.��B^9��M'G��i��t���*~������t�ů$���L,�*.*(rE���v��ݪc�{��݁ա��ɭ{܌�]���PY>��PJ��z3�#X�ѶC�Z�vl��lɲ,�3�Z^      !      x�3�N�+I�KN�2��/J����� Q      #   b   x�3�t��OQ��/���K�>��TW�N��)'w�\u���3����9�K��*�KN�D�1��H���W�/�I��89;'�T�N��Y9)`5�\1z\\\ �)2      %     x�u�]o�0��˯��[��F`W���Щ�h�A����`�m�맙nɒ%O����Ɂ@� ��U��)�����4Y^�#h�]���)<�/�4��(x��Im?�����Z��'�����F��=�YH�VS������pպ�aH~t��]GY|�,4I�hL7t���Y5�R���q�O^(�8��*M)�0�d��>x���H���\<�Ӆ�0���"����kO��8j�4	^sƬ I���'xVj�zw`��P�к`bk����ӆd!ck��SVtB     