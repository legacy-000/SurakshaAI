-- KSP SURAKSHA AI - 26 KSP Tables
-- Version 1.0

CREATE TABLE IF NOT EXISTS CaseMaster (
    CaseMasterID INT PRIMARY KEY,
    CrimeNo VARCHAR(50),
    CaseNo VARCHAR(50),
    CrimeRegisteredDate DATE,
    PolicePersonID INT,
    PoliceStationID INT,
    CaseCategoryID INT,
    GravityOffenceID INT,
    CrimeMajorHeadID INT,
    CrimeMinorHeadID INT,
    CaseStatusID INT,
    CourtID INT,
    IncidentFromDate DATETIME,
    IncidentToDate DATETIME,
    InfoReceivedPSDate DATETIME,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    BriefFacts NVARCHAR(MAX)
);

CREATE TABLE IF NOT EXISTS ComplainantDetails (
    ComplainantID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    ComplainantName VARCHAR(200),
    AgeYear INT,
    OccupationID INT,
    ReligionID INT,
    CasteID INT,
    GenderID INT
);

CREATE TABLE IF NOT EXISTS Victim (
    VictimMasterID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    VictimName VARCHAR(200),
    AgeYear INT,
    GenderID INT,
    VictimPolice VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS Accused (
    AccusedMasterID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    AccusedName VARCHAR(200),
    AgeYear INT,
    GenderID INT,
    PersonID VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS ArrestSurrender (
    ArrestSurrenderID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    ArrestSurrenderTypeID INT,
    ArrestSurrenderDate DATE,
    ArrestSurrenderStateId INT,
    ArrestSurrenderDistrictId INT,
    PoliceStationID INT,
    IOID INT,
    CourtID INT,
    AccusedMasterID INT,
    IsAccused BIT,
    IsComplainantAccused BIT
);

CREATE TABLE IF NOT EXISTS ChargesheetDetails (
    CSID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    csdate DATETIME,
    cstype CHAR(1),
    PolicePersonID INT
);

CREATE TABLE IF NOT EXISTS Act (
    ActCode VARCHAR(20) PRIMARY KEY,
    ActDescription VARCHAR(200),
    ShortName VARCHAR(50),
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Section (
    ActCode VARCHAR(20),
    SectionCode VARCHAR(20),
    SectionDescription VARCHAR(200),
    Active BIT DEFAULT 1,
    PRIMARY KEY (ActCode, SectionCode)
);

CREATE TABLE IF NOT EXISTS ActSectionAssociation (
    AssociationID INT PRIMARY KEY,
    CaseMasterID INT NOT NULL,
    ActID INT,
    SectionID INT,
    ActOrderID INT,
    SectionOrderID INT
);

CREATE TABLE IF NOT EXISTS CrimeHead (
    CrimeHeadID INT PRIMARY KEY,
    CrimeGroupName VARCHAR(200),
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS CrimeSubHead (
    CrimeSubHeadID INT PRIMARY KEY,
    CrimeHeadID INT NOT NULL,
    CrimeHeadName VARCHAR(200),
    SeqID INT
);

CREATE TABLE IF NOT EXISTS CrimeHeadActSection (
    CrimeHeadID INT NOT NULL,
    ActCode VARCHAR(20),
    SectionCode VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS CasteMaster (
    caste_master_id INT PRIMARY KEY,
    caste_master_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS ReligionMaster (
    ReligionID INT PRIMARY KEY,
    ReligionName VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS OccupationMaster (
    OccupationID INT PRIMARY KEY,
    OccupationName VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS CaseCategory (
    CaseCategoryID INT PRIMARY KEY,
    LookupValue VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS GravityOffence (
    GravityOffenceID INT PRIMARY KEY,
    LookupValue VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS CaseStatusMaster (
    CaseStatusID INT PRIMARY KEY,
    CaseStatusName VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Court (
    CourtID INT PRIMARY KEY,
    CourtName VARCHAR(200),
    DistrictID INT,
    StateID INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS District (
    DistrictID INT PRIMARY KEY,
    DistrictName VARCHAR(100),
    StateID INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS State (
    StateID INT PRIMARY KEY,
    StateName VARCHAR(100),
    NationalityID INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Unit (
    UnitID INT PRIMARY KEY,
    UnitName VARCHAR(200),
    TypeID INT,
    ParentUnit INT,
    NationalityID INT,
    StateID INT,
    DistrictID INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS UnitType (
    UnitTypeID INT PRIMARY KEY,
    UnitTypeName VARCHAR(100),
    CityDistState VARCHAR(50),
    Hierarchy INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Rank (
    RankID INT PRIMARY KEY,
    RankName VARCHAR(100),
    Hierarchy INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Designation (
    DesignationID INT PRIMARY KEY,
    DesignationName VARCHAR(100),
    SortOrder INT,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Employee (
    EmployeeID INT PRIMARY KEY,
    DistrictID INT,
    UnitID INT,
    RankID INT,
    DesignationID INT,
    KGID VARCHAR(20),
    FirstName VARCHAR(100),
    EmployeeDOB DATE,
    GenderID INT,
    BloodGroupID INT,
    PhysicallyChallenged BIT,
    AppointmentDate DATE
);
