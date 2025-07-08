CREATE TABLE participants (
	pid char(24) PRIMARY KEY,
	passed_colorblindness boolean DEFAULT false,
	attempted_colorblindness boolean DEFAULT false,
	passed_comprehension boolean DEFAULT null,
	attempted_comprehension boolean DEFAULT false
)

Drop table participants

SELECT pid as "Prolific ID",
	   passed_colorblindness as "Did the user already pass the Colorblindness Check?",
	   attempted_colorblindness as "Has the user already attempted the Colorblindness Check?",
	   passed_comprehension as "Did the user already pass the Comprehension Check?",
	   attempted_comprehension as "Has the user already attempted the Comprehension Check?",
	   ishihara_test_cards as "What are the images that we will show the user?"
FROM participants


INSERT INTO participants (pid)
	VALUES('test123');

DELETE FROM participants
WHERE pid='test123';

/*Add the ishihara_test_cards column as an array of path strings to track the test cards provided for each participant*/
ALTER TABLE participants  
ADD COLUMN ishihara_test_cards text[];

CREATE TABLE ishihara (
	file_path text PRIMARY KEY,
	correct_digit smallint, /*A single digit (i.e. integer in [0,9])*/
	color_palette smallint /*A single digit to describe the color palette of the ishihara test card -> currently four different palettes*/
)

/* Insert four initial Ishihara test cards */
INSERT INTO ishihara VALUES
	('images/0_AveriaLibre-LightItalictheme_1 type_1.png', 0, 1),
	('images/0_AveriaLibre-LightItalictheme_2 type_2.png', 0, 2),
	('images/0_AveriaLibre-LightItalictheme_3 type_3.png', 0, 3),
	('images/0_AveriaLibre-LightItalictheme_4 type_3.png', 0, 4);

/* Get one random image from each color palette and show images in random order*/

SELECT file_path /*, color_palette*/
FROM (
	/*
		Select one random image from each color palette.
		This works because the PostgreSQL DISTINCT ON clause is applied to the 
		result of each group only AFTER sorting the rows in that group!
	*/
	SELECT DISTINCT on (color_palette) file_path, color_palette 
	FROM ishihara
	ORDER BY color_palette, random()
) as distinct_images
ORDER BY random() /* Outer query simply receives the random image of each group and reorders them randomly */

/* Does the same as but results into a randomly sorted text array of file paths */
SELECT array_agg(file_path ORDER BY random()) as random_image_paths
FROM (
    SELECT DISTINCT ON (color_palette) file_path
    FROM ishihara
    ORDER BY color_palette, random()
) as distinct_images;

/*We can now use this query to update ishihara_test_cards column of a given PID */
UPDATE participants
SET ishihara_test_cards = (
	SELECT array_agg(file_path ORDER BY random()) as random_image_paths
	FROM (
		SELECT DISTINCT ON (color_palette) file_path
		FROM ishihara
		ORDER BY color_palette, random()
	) as distinct_images
)
WHERE pid = 'test123'

/* Update query with escaped single quote within text */
UPDATE ishihara 
SET correct_digit = 'I don''t see a digit' 
WHERE file_path like '%Perpetua%';