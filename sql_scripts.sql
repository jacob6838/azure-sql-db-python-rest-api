CREATE TABLE ApiKeysDev (
    ID int NOT NULL IDENTITY(1,1),
    ApiKeyHash varchar(64) NOT NULL UNIQUE,
	UserName varchar(32),
    Email varchar(320),
    DateCreated DATETIME NOT NULL,
    DateUpdated DATETIME,
	IsDeleted bit,
);

CREATE PROCEDURE create_key @key varchar(64)
AS
insert into ApiKeys (ApiKeyHash, DateCreated)
values(@key, GETDATE())
GO;

CREATE PROCEDURE create_key_with_email @key varchar(64), @email varchar(254)
AS
insert into ApiKeys (ApiKeyHash, Email, DateCreated)
values(@key, @email, GETDATE())
GO;

CREATE PROCEDURE delete_key @key varchar(64)
AS
delete from ApiKeys where ApiKeyHash = @key
GO;

CREATE PROCEDURE find_key @key varchar(64)
AS
select 1 from ApiKeys where ApiKeyHash = @key and (IsDeleted IS NULL OR IsDeleted <> 1)
GO;