CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE User (
  user_id int4 AUTO_INCREMENT,
  email varchar(255) UNIQUE NOT NULL,
  password varchar(255),
  hometown varchar(20),
  bio varchar(280),
  propic varchar(255),
  fname varchar(20),
  lname varchar(20),
  gender varchar(10),
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
  name varchar(20) UNIQUE NOT NULL,
  date char(10),
  FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  PRIMARY KEY (album_id)
);

CREATE TABLE Photo (
  photo_id int4 AUTO_INCREMENT,
  album_id int4 NOT NULL,
  caption VARCHAR(255),
  photo_path varchar(255) UNIQUE NOT NULL,
  FOREIGN KEY (album_id) REFERENCES User_Album(album_id) ON DELETE CASCADE,
  PRIMARY KEY (photo_id)
);


/* here we put email as a attribute.
normally, we couldn't because there comments can belong to no one
but we will generalize this "no one" as a pretend user "Anonymous"
*/
CREATE TABLE Photo_Comment (
  comment_id int4 AUTO_INCREMENT,
  photo_id int4 NOT NULL,
  email varchar(255),
  text varchar(280),
  date char(10),
  FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE,
  FOREIGN KEY (email) REFERENCES User(email) ON DELETE CASCADE,
  PRIMARY KEY (comment_id)
);

/* to track which users liked a given photo
*/
CREATE TABLE Photo_Like(
  user_id int4,
  photo_id int4,
  CONSTRAINT Pk_Photo_Like PRIMARY KEY (user_id, photo_id),
  FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE
);

CREATE TABLE Tag (
  word varchar(20),
  PRIMARY KEY(word)
);

/* a tag must belong to at least one photo
*/
CREATE TABLE Photo_Tag (
  word varchar(20),
  photo_id int4,
  CONSTRAINT Pk_Photo_Tag PRIMARY KEY (word, photo_id),
  FOREIGN KEY (photo_id) REFERENCES Photo(photo_id) ON DELETE CASCADE
);

INSERT INTO User (email, password) VALUES ('photoshare@bu.edu', 'password');
