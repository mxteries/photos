CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE User (
  user_id int4 AUTO_INCREMENT,
  email varchar(255) UNIQUE NOT NULL,
  password varchar(255),
  hometown varchar(20),
  bio varchar(280),
  propic longblob,
  fname varchar(20),
  lname varchar(20),
  gender varchar(10),
  contribution int,
  PRIMARY KEY (user_id)
);

/* perhaps add a "since" */
CREATE TABLE Friendship (
  follower_user_id int4,
  followed_user_id int4,
  FOREIGN KEY (follower_user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  FOREIGN KEY (followed_user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  CONSTRAINT PK_Friend PRIMARY KEY (follower_user_id, followed_user_id)
);

CREATE TABLE User_Album (
  album_id int4 AUTO_INCREMENT,
  user_id int4 NOT NULL,
  name varchar(20),
  date char(10),
  FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  PRIMARY KEY (album_id)
);

CREATE TABLE Photo (
  photo_id int4 AUTO_INCREMENT,
  album_id int4 NOT NULL,
  caption VARCHAR(255),
  likes int,
  imgdata longblob,
  FOREIGN KEY (album_id) REFERENCES User_Album(album_id) ON DELETE CASCADE,
  PRIMARY KEY (photo_id)
);

CREATE TABLE Photo_Comment (
  comment_id int4 AUTO_INCREMENT,
  photo_id int4 NOT NULL,
  text varchar(280),
  date char(10),
  FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE,
  PRIMARY KEY (comment_id)
);

CREATE TABLE Tag (
  word varchar(20),
  PRIMARY KEY(word)
);

/* tag to photo is many to many now, no participation constraints
*/
CREATE TABLE Photo_Tag (
  word varchar(20),
  photo_id int4,
  CONSTRAINT Pk_Photo_Tag PRIMARY KEY (word, photo_id)
);


INSERT INTO User (email, password) VALUES ('photoshare@bu.edu', 'password');
INSERT INTO User (email, password) VALUES ('ash@bu.edu', 'password');