/* =========================================================
   DROP EXISTING TABLES
   ========================================================= */

DROP TABLE IF EXISTS Telemetry;
DROP TABLE IF EXISTS Laps;
DROP TABLE IF EXISTS Weather;
DROP TABLE IF EXISTS Corners;
DROP TABLE IF EXISTS Driver_Entries;
DROP TABLE IF EXISTS Sessions;
DROP TABLE IF EXISTS Teams;
DROP TABLE IF EXISTS Drivers;
DROP TABLE IF EXISTS Races;


/* =========================================================
   RACES
   ========================================================= */

CREATE TABLE Races
(
    RaceID VARCHAR(50) NOT NULL,
    RoundNumber INT NOT NULL,
    Country VARCHAR(100),
    Location VARCHAR(100),
    OfficialEventName VARCHAR(200),
    EventDate DATETIME2,
    EventName VARCHAR(100),
    EventFormat VARCHAR(100),
    F1ApiSupport VARCHAR(50),
    Year INT NOT NULL,
    TrackLength FLOAT,
    No_of_Laps INT,
    Time_Saved_per_Lap_Fuel FLOAT,

    CONSTRAINT PK_Races
        PRIMARY KEY (RaceID),

    CONSTRAINT UQ_Races_Year_Round
        UNIQUE (Year, RoundNumber)
);


/* =========================================================
   SESSIONS
   ========================================================= */

CREATE TABLE Sessions
(
    RaceID VARCHAR(50) NOT NULL,
    SessionNo INT NOT NULL,
    SessionName VARCHAR(100),
    SessionDate DATETIME2,
    SessionDateUtc DATETIME2,
    SessionID VARCHAR(50) NOT NULL,

    CONSTRAINT PK_Sessions
        PRIMARY KEY (SessionID),

    CONSTRAINT FK_Sessions_Races
        FOREIGN KEY (RaceID)
        REFERENCES Races(RaceID),

    CONSTRAINT UQ_Sessions_Race_Session
        UNIQUE (RaceID, SessionNo)
);


/* =========================================================
   CORNERS
   ========================================================= */

CREATE TABLE Corners
(
    X FLOAT,
    Y FLOAT,
    Number INT,
    Letter VARCHAR(10),
    Angle FLOAT,
    Distance FLOAT,

    RaceID VARCHAR(50) NOT NULL,
    CornerID VARCHAR(100) NOT NULL,

    CONSTRAINT PK_Corners
        PRIMARY KEY (CornerID),

    CONSTRAINT FK_Corners_Races
        FOREIGN KEY (RaceID)
        REFERENCES Races(RaceID)
);


/* =========================================================
   WEATHER
   ========================================================= */

CREATE TABLE Weather
(
    Time FLOAT,
    AirTemp FLOAT,
    Humidity FLOAT,
    Pressure FLOAT,
    Rainfall FLOAT,
    TrackTemp FLOAT,
    WindDirection FLOAT,
    WindSpeed FLOAT,

    SessionID VARCHAR(50) NOT NULL,
    WeatherID VARCHAR(100) NOT NULL,

    CONSTRAINT PK_Weather
        PRIMARY KEY (WeatherID),

    CONSTRAINT FK_Weather_Sessions
        FOREIGN KEY (SessionID)
        REFERENCES Sessions(SessionID)
);


/* =========================================================
   DRIVERS
   ========================================================= */

CREATE TABLE Drivers
(
    BroadcastName VARCHAR(100),
    Abbreviation VARCHAR(10) NOT NULL,
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    HeadshotUrl VARCHAR(500),
    FullName VARCHAR(100) NOT NULL,

    DriverID BIGINT IDENTITY(1,1) NOT NULL,

    CONSTRAINT PK_Drivers
        PRIMARY KEY (DriverID),

    CONSTRAINT UQ_Drivers_FullName
        UNIQUE (FullName)
);


/* =========================================================
   TEAMS
   ========================================================= */

CREATE TABLE Teams
(
    TeamID BIGINT IDENTITY(1,1) NOT NULL,
    Team VARCHAR(100) NOT NULL,
    TeamColor VARCHAR(20),

    CONSTRAINT PK_Teams
        PRIMARY KEY (TeamID),

    CONSTRAINT UQ_Teams_Team
        UNIQUE (Team)
);


/* =========================================================
   DRIVER ENTRIES
   ========================================================= */

CREATE TABLE Driver_Entries
(
    EntryID VARCHAR(100) NOT NULL,
    DriverID BIGINT NOT NULL,
    TeamID BIGINT NOT NULL,
    SessionID VARCHAR(50) NOT NULL,
    DriverNumber VARCHAR(20),

    CONSTRAINT PK_Driver_Entries
        PRIMARY KEY (EntryID),

    CONSTRAINT FK_Driver_Entries_Drivers
        FOREIGN KEY (DriverID)
        REFERENCES Drivers(DriverID),

    CONSTRAINT FK_Driver_Entries_Teams
        FOREIGN KEY (TeamID)
        REFERENCES Teams(TeamID),

    CONSTRAINT FK_Driver_Entries_Sessions
        FOREIGN KEY (SessionID)
        REFERENCES Sessions(SessionID),

    CONSTRAINT UQ_Driver_Entries
        UNIQUE (SessionID, DriverID, DriverNumber)
);


/* =========================================================
   LAPS
   ========================================================= */

CREATE TABLE Laps (
    LapID VARCHAR(150) NOT NULL,
    EntryID VARCHAR(100) NOT NULL,
    SessionID VARCHAR(50) NOT NULL,

    Time FLOAT,
    LapNumber INT,
    Stint INT,

    PitOutTime FLOAT,
    PitInTime FLOAT,

    Sector1Time FLOAT,
    Sector2Time FLOAT,
    Sector3Time FLOAT,

    Sector1SessionTime FLOAT,
    Sector2SessionTime FLOAT,
    Sector3SessionTime FLOAT,

    SpeedI1 FLOAT,
    SpeedI2 FLOAT,
    SpeedFL FLOAT,
    SpeedST FLOAT,

    IsPersonalBest BIT,

    Compound VARCHAR(50),
    TyreLife FLOAT,
    FreshTyre BIT,

    LapStartTime FLOAT,
    LapStartDate DATETIME2,

    TrackStatus VARCHAR(50),
    Position INT,

    Deleted BIT,
    DeletedReason VARCHAR(500),

    LapTimeSeconds FLOAT,
    LapIntoStint INT,
    QuickLap_Binary BIT,
    FuelAdjustedLapTime FLOAT,

    CONSTRAINT PK_Laps
        PRIMARY KEY (LapID),

    CONSTRAINT FK_Laps_Driver_Entries
        FOREIGN KEY (EntryID)
        REFERENCES Driver_Entries(EntryID),

    CONSTRAINT FK_Laps_Sessions
        FOREIGN KEY (SessionID)
        REFERENCES Sessions(SessionID)
);



/* =========================================================
   TELEMETRY
   =========================================================

   IMPORTANT:

   SessionID is deliberately NOT a foreign key.

   This allows telemetry to exist at session level even when
   there is no corresponding LapID.

   Example:
       Car in garage
       Installation lap
       Pre-lap telemetry
       Other telemetry not associated with a lap

   LapID IS a foreign key, but is nullable.
   ========================================================= */

CREATE TABLE Telemetry
(
    Date DATETIME2,
    RPM FLOAT,
    Speed FLOAT,
    nGear INT,
    Throttle FLOAT,
    Brake BIT,
    DRS INT,
    Source VARCHAR(50),

    Time FLOAT,
    SessionTime FLOAT,
    Distance FLOAT,

    LapStartDate DATETIME2,
    LapNumber INT,
    TimeThroughLap FLOAT,

    X FLOAT,
    Y FLOAT,
    Z FLOAT,

    SessionID VARCHAR(50) NOT NULL,

    LapID VARCHAR(150) NULL,

    TelemetryID VARCHAR(200) NOT NULL,

    CONSTRAINT PK_Telemetry
        PRIMARY KEY (TelemetryID),

    CONSTRAINT FK_Telemetry_Laps
        FOREIGN KEY (LapID)
        REFERENCES Laps(LapID)
);


/* =========================================================
   INDEXES
   =========================================================

   These are important for the fast append system we will
   build next.
   ========================================================= */


/* ---------------------------------------------------------
   RACES
   --------------------------------------------------------- */

CREATE INDEX IX_Races_RaceID
    ON Races(RaceID);


/* ---------------------------------------------------------
   SESSIONS
   --------------------------------------------------------- */

CREATE INDEX IX_Sessions_RaceID
    ON Sessions(RaceID);


/* ---------------------------------------------------------
   CORNERS
   --------------------------------------------------------- */

CREATE INDEX IX_Corners_RaceID
    ON Corners(RaceID);


/* ---------------------------------------------------------
   WEATHER
   --------------------------------------------------------- */

CREATE INDEX IX_Weather_SessionID
    ON Weather(SessionID);


/* ---------------------------------------------------------
   DRIVER ENTRIES
   --------------------------------------------------------- */

CREATE INDEX IX_Driver_Entries_SessionID_DriverNumber
    ON Driver_Entries(SessionID, DriverNumber);

CREATE INDEX IX_Driver_Entries_DriverID
    ON Driver_Entries(DriverID);

CREATE INDEX IX_Driver_Entries_TeamID
    ON Driver_Entries(TeamID);


/* ---------------------------------------------------------
   LAPS
   --------------------------------------------------------- */

CREATE INDEX IX_Laps_EntryID
    ON Laps(EntryID);

CREATE INDEX IX_Laps_SessionID
    ON Laps(SessionID);


/* ---------------------------------------------------------
   TELEMETRY
   ---------------------------------------------------------

   SessionID is indexed even though it isn't a foreign key.
   This makes session-level telemetry queries fast.

   LapID is also indexed for telemetry ? lap queries.
   --------------------------------------------------------- */

CREATE INDEX IX_Telemetry_SessionID
    ON Telemetry(SessionID);

CREATE INDEX IX_Telemetry_LapID
    ON Telemetry(LapID);


/* =========================================================
   DROP EXISTING STAGING TABLES
   ========================================================= */

DROP TABLE IF EXISTS Upload_Telemetry;
DROP TABLE IF EXISTS Upload_Laps;
DROP TABLE IF EXISTS Upload_Weather;
DROP TABLE IF EXISTS Upload_Corners;
DROP TABLE IF EXISTS Upload_Driver_Entries;
DROP TABLE IF EXISTS Upload_Sessions;
DROP TABLE IF EXISTS Upload_Teams;
DROP TABLE IF EXISTS Upload_Drivers;
DROP TABLE IF EXISTS Upload_Races;


/* =========================================================
   UPLOAD_RACES
   ========================================================= */

CREATE TABLE Upload_Races
(
    RoundNumber INT,
    Country VARCHAR(100),
    Location VARCHAR(100),
    OfficialEventName VARCHAR(200),
    EventDate DATETIME2,
    EventName VARCHAR(100),
    EventFormat VARCHAR(100),
    F1ApiSupport VARCHAR(50),
    Year INT,
    RaceID VARCHAR(50),

    TrackLength FLOAT,
    No_of_Laps INT,
    Time_Saved_per_Lap_Fuel FLOAT
);


/* =========================================================
   UPLOAD_DRIVERS
   ========================================================= */

CREATE TABLE Upload_Drivers
(
    BroadcastName VARCHAR(100),
    Abbreviation VARCHAR(10),
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    HeadshotUrl VARCHAR(500),
    FullName VARCHAR(100),

    DriverID BIGINT
);


/* =========================================================
   UPLOAD_TEAMS
   ========================================================= */

CREATE TABLE Upload_Teams
(
    TeamID BIGINT,
    Team VARCHAR(100),
    TeamColor VARCHAR(20)
);


/* =========================================================
   UPLOAD_SESSIONS
   ========================================================= */

CREATE TABLE Upload_Sessions
(
    RaceID VARCHAR(50),
    SessionNo INT,
    SessionName VARCHAR(100),
    SessionDate DATETIME2,
    SessionDateUtc DATETIME2,
    SessionID VARCHAR(50)
);


/* =========================================================
   UPLOAD_CORNERS
   ========================================================= */

CREATE TABLE Upload_Corners
(
    X FLOAT,
    Y FLOAT,
    Number INT,
    Letter VARCHAR(10),
    Angle FLOAT,
    Distance FLOAT,

    RaceID VARCHAR(50),
    CornerID VARCHAR(100)
);


/* =========================================================
   UPLOAD_WEATHER
   ========================================================= */

CREATE TABLE Upload_Weather
(
    Time FLOAT,
    AirTemp FLOAT,
    Humidity FLOAT,
    Pressure FLOAT,
    Rainfall FLOAT,
    TrackTemp FLOAT,
    WindDirection FLOAT,
    WindSpeed FLOAT,

    SessionID VARCHAR(50),
    WeatherID VARCHAR(100)
);


/* =========================================================
   UPLOAD_DRIVER_ENTRIES
   ========================================================= */

CREATE TABLE Upload_Driver_Entries (
    EntryID VARCHAR(100) NOT NULL,
    SessionID VARCHAR(50) NOT NULL,
    DriverNumber VARCHAR(20),
    FullName VARCHAR(100),
    Team VARCHAR(100)
);


/* =========================================================
   UPLOAD_LAPS
   ========================================================= */

CREATE TABLE Upload_Laps (
    LapID VARCHAR(150),
    EntryID VARCHAR(100),
    SessionID VARCHAR(50),

    Time FLOAT,
    LapNumber INT,
    Stint INT,

    PitOutTime FLOAT,
    PitInTime FLOAT,

    Sector1Time FLOAT,
    Sector2Time FLOAT,
    Sector3Time FLOAT,

    Sector1SessionTime FLOAT,
    Sector2SessionTime FLOAT,
    Sector3SessionTime FLOAT,

    SpeedI1 FLOAT,
    SpeedI2 FLOAT,
    SpeedFL FLOAT,
    SpeedST FLOAT,

    IsPersonalBest BIT,

    Compound VARCHAR(50),
    TyreLife FLOAT,
    FreshTyre BIT,

    LapStartTime FLOAT,
    LapStartDate DATETIME2,

    TrackStatus VARCHAR(50),
    Position INT,

    Deleted BIT,
    DeletedReason VARCHAR(500),

    LapTimeSeconds FLOAT,
    LapIntoStint INT,
    QuickLap_Binary BIT,
    FuelAdjustedLapTime FLOAT
);


/* =========================================================
   UPLOAD_TELEMETRY
   ========================================================= */

CREATE TABLE Upload_Telemetry
(
    Date DATETIME2,

    RPM FLOAT,
    Speed FLOAT,
    nGear INT,
    Throttle FLOAT,
    Brake BIT,
    DRS INT,
    Source VARCHAR(50),

    Time FLOAT,
    SessionTime FLOAT,
    Distance FLOAT,

    LapStartDate DATETIME2,
    LapNumber INT,
    TimeThroughLap FLOAT,

    X FLOAT,
    Y FLOAT,
    Z FLOAT,

    SessionID VARCHAR(50),
    LapID VARCHAR(150),

    TelemetryID VARCHAR(200)
);
