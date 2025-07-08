
-- Drop tables if they exist
DROP TABLE IF EXISTS participants;
DROP TABLE IF EXISTS attention_check_images;
DROP TABLE IF EXISTS modified_images;
DROP TABLE IF EXISTS real_images;
DROP TABLE IF EXISTS ishihara_test_cards;
DROP TABLE IF EXISTS comprehension_check_images;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS site_logs;
DROP TABLE IF EXISTS image_logs;
DROP TABLE IF EXISTS leaderboard;
DROP TABLE IF EXISTS ratings_per_real_image;
DROP TABLE IF EXISTS ratings_per_modified_image;

-- Create tables
CREATE TABLE participants (
    pid char(24) PRIMARY KEY,
    study_id text NOT NULL,
    session_id text NOT NULL,
    attempted_colorblindness boolean DEFAULT false,
    passed_colorblindness boolean DEFAULT null,
    attempted_comprehension boolean DEFAULT false,
    passed_comprehension boolean DEFAULT null,
    ishihara_test_cards int[] DEFAULT null,
    colorblind_answers text[] DEFAULT null,
    correct_digits text[] DEFAULT null,
    main_study_images int[] DEFAULT null,
    main_study_answers text[] DEFAULT null,
    completed_study boolean DEFAULT false,
    comprehension_check_images int[] DEFAULT null,
    comprehension_check_answers text[] DEFAULT null,
    correct_comprehension_check_answers int[] DEFAULT null,
    real_indices int[] DEFAULT null,
    modified_indices int[] DEFAULT null,
    atc_indices int[] DEFAULT null,
    imc_indices int[] DEFAULT null,
    correct_imc_values text[] DEFAULT null
);

CREATE TABLE attention_check_images (
    id int PRIMARY KEY,
    image bytea,
    is_imc boolean,
    correct_value varchar(255) DEFAULT null
);

CREATE TABLE ishihara_test_cards (
    id int PRIMARY KEY,
    image bytea,
    color_type varchar(255),
    digit varchar(255)
);

CREATE TABLE modified_images (
    id int PRIMARY KEY,
    image bytea,
    model_name varchar(255),
    attack_name varchar(255)
);

CREATE TABLE real_images (
    id int PRIMARY KEY,
    image bytea,
    model_name varchar(255)
);

CREATE TABLE comprehension_check_images (
    id int PRIMARY KEY,
    image bytea,
    is_modified boolean,
    modification varchar(255),
    class varchar(255),
    img_number varchar(1)
);

CREATE TABLE feedback (
    pid char(24) PRIMARY KEY,
    feedback text,
    self_assessment text[]
);

CREATE TABLE site_logs(
	pid char(24),
	url text,
	time timestamp,
	PRIMARY KEY (pid, url, time)
);

CREATE TABLE image_logs(
    pid char(24),
    index int,
    time timestamp,
    PRIMARY KEY (pid, index, time)
);

CREATE TABLE ratings_per_real_image (
    id int PRIMARY KEY,
    image bytea,
    ratings text[],
    model_name varchar(255)
);

CREATE TABLE ratings_per_modified_image (
    id int PRIMARY KEY,
    image bytea,
    ratings text[],
    model_name varchar(255),
    attack_name varchar(255)
);

CREATE TABLE leaderboard (
    id char(24) PRIMARY KEY,
    user_name VARCHAR(50) UNIQUE,
    total_accuracy FLOAT,
    real_accuracy FLOAT,
    modified_accuracy FLOAT,
    check_accuracy FLOAT,
    borda_score INT,
    model_name varchar(255),
    attack_name varchar(255)
);

-- Create a function to add a new user to the leaderboard
CREATE OR REPLACE FUNCTION add_user(
    p_id CHAR(24),
    p_user_name VARCHAR,
    p_total_accuracy FLOAT,
    p_real_accuracy FLOAT,
    p_modified_accuracy FLOAT,
    p_check_accuracy FLOAT,
    p_model_name VARCHAR,
    p_attack_name VARCHAR
)
RETURNS VOID AS $$
BEGIN
    -- Insert the new user
    INSERT INTO leaderboard (id, user_name, total_accuracy, real_accuracy, modified_accuracy, check_accuracy, model_name, attack_name)
    VALUES (p_id, p_user_name, p_total_accuracy, p_real_accuracy, p_modified_accuracy, p_check_accuracy, p_model_name, p_attack_name);

    -- Recalculate ranks and update Borda scores
    DROP TABLE IF EXISTS ranks;

    CREATE TEMP TABLE ranks AS
    SELECT
        id,
        DENSE_RANK() OVER (ORDER BY total_accuracy ASC) AS rank_total_accuracy,
        DENSE_RANK() OVER (ORDER BY real_accuracy ASC) AS rank_real_accuracy,
        DENSE_RANK() OVER (ORDER BY modified_accuracy ASC) AS rank_modified_accuracy,
        DENSE_RANK() OVER (ORDER BY check_accuracy ASC) AS rank_check_accuracy
    FROM
        leaderboard
    WHERE
        model_name = p_model_name AND attack_name = p_attack_name;

    UPDATE leaderboard
    SET borda_score = (
        SELECT rank_total_accuracy + rank_real_accuracy + rank_modified_accuracy + rank_check_accuracy
        FROM ranks
        WHERE ranks.id = leaderboard.id and model_name = p_model_name and attack_name = p_attack_name
    )
    WHERE leaderboard.model_name = p_model_name AND leaderboard.attack_name = p_attack_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_leaderboard_entry(
    p_id CHAR(24),
    p_model_name VARCHAR,
    p_attack_name VARCHAR
)
RETURNS VOID AS $$
BEGIN

    -- Delete the user from the leaderboard
    DELETE FROM leaderboard WHERE id = p_id and model_name = p_model_name and attack_name = p_attack_name;



    -- Recalculate ranks and update Borda scores
    DROP TABLE IF EXISTS ranks;

    CREATE TEMP TABLE ranks AS
    SELECT
        id,
        DENSE_RANK() OVER (ORDER BY total_accuracy ASC) AS rank_total_accuracy,
        DENSE_RANK() OVER (ORDER BY real_accuracy ASC) AS rank_real_accuracy,
        DENSE_RANK() OVER (ORDER BY modified_accuracy ASC) AS rank_modified_accuracy,
        DENSE_RANK() OVER (ORDER BY check_accuracy ASC) AS rank_check_accuracy
    FROM
        leaderboard
    WHERE
        leaderboard.model_name = p_model_name AND leaderboard.attack_name = p_attack_name;

    UPDATE leaderboard
    SET borda_score = (
        SELECT rank_total_accuracy + rank_real_accuracy + rank_modified_accuracy + rank_check_accuracy
        FROM ranks
        WHERE ranks.id = leaderboard.id and leaderboard.model_name = p_model_name and leaderboard.attack_name = p_attack_name
    )
    WHERE leaderboard.model_name = p_model_name AND leaderboard.attack_name = p_attack_name;
END;
$$ LANGUAGE plpgsql;

-- -- Create a temporary table to store the path
-- CREATE TEMP TABLE temp_path (path text);

-- -- Insert the path into the temporary table
-- INSERT INTO temp_path (path) VALUES (:'data_path');

-- -- Use a DO block to execute the COPY commands
-- DO $$
-- DECLARE
--     file_paths text[] := array[
--         'attention_check_images.csv',
--         'ishihara_test_cards.csv',
--         'modified_images.csv',
--         'real_images.csv',
--         'comprehension_check_images.csv'
--     ];
--     base_path text;
--     full_path text;
--     table_name text;
-- BEGIN
--     -- Retrieve the base path from the temporary table
--     SELECT path INTO base_path FROM temp_path LIMIT 1;

--     FOREACH full_path IN ARRAY file_paths LOOP
--         full_path := base_path || full_path;
--         table_name := split_part(full_path, '/', -1);
--         table_name := left(table_name, length(table_name) - 4); -- Remove the ".csv" extension
--         EXECUTE 'COPY ' || table_name || ' FROM ''' || full_path || ''' WITH (FORMAT csv, HEADER false)';
--     END LOOP;
-- END $$;
