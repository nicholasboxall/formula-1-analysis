# -*- coding: utf-8 -*-
"""
Import Data
"""

import pandas as pd
import fastf1
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta

start_time = time.time()


fastf1.Cache.enable_cache("C:/Users/nicho/AppData/Local/Temp/fastf1")

# ============================================================
# RACES TO LOAD
# ============================================================

races_to_load = [
    (2025, "United States")
]

send_to_sql = True

server = r"DESKTOP-1Q9PKTR"

#database = "F1_Analysis"
database = "F1Analytics_Individual"

# ============================================================
# MASTER LISTS
# ============================================================

all_races = []
all_sessions = []
all_corners = []

all_weather = []
all_laps = []
all_telemetry = []

all_driver_info = []
all_team_info = []


# ============================================================
# LOOP THROUGH EACH RACE
# ============================================================

for year, event in races_to_load:
    
    # ========================================================
    # RACE SCHEDULE
    # ========================================================

    races_year = fastf1.get_event_schedule(year)

    races_year = races_year[
        races_year["RoundNumber"] != 0
    ].copy()

    races_year["Year"] = year
    
    races_year["RaceID"] = (
        races_year["Year"].astype(str)
        + "-"
        + races_year["RoundNumber"].astype(str)
    )
    
    roundnumber = races_year.get_event_by_name(
        event
    )["RoundNumber"]
    
    race_id = races_year.loc[
        races_year["RoundNumber"] == roundnumber,
        "RaceID"
    ].iloc[0]
    
    # ========================================================
    # SPLIT INTO SESSIONS
    # ========================================================

    sessions_year = []

    for _, race in races_year.iterrows():

        for i in range(1, 6):

            session_name = race[f"Session{i}"]
            session_date = race[f"Session{i}Date"]
            session_date_utc = race[f"Session{i}DateUtc"]

            if pd.notna(session_name):

                sessions_year.append({
                    "RaceID": race["RaceID"],
                    "RoundNumber": race["RoundNumber"],
                    "SessionNo": i,
                    "SessionName": session_name,
                    "SessionDate": session_date,
                    "SessionDateUtc": session_date_utc
                })


    sessions_year = pd.DataFrame(
        sessions_year
    )


    # ========================================================
    # SESSION PRIMARY KEY
    #
    # SessionID = RaceID + SessionNo
    #
    # Example:
    # 2025-14-1
    # 2025-14-2
    # 2026-16-1
    # ========================================================

    sessions_year["SessionID"] = (
        sessions_year["RaceID"].astype(str)
        + "-"
        + sessions_year["SessionNo"].astype(str)
    )


    # ========================================================
    # ADD RACES AND SESSIONS TO MASTER LISTS
    # ========================================================

    all_races.append(
        races_year
    )

    all_sessions.append(
        sessions_year
    )


    # ========================================================
    # GET SESSION DATES FOR THIS RACE
    # ========================================================

    session_time = sessions_year[
        sessions_year["RaceID"] == race_id
    ]["SessionDateUtc"]

    session_time = (
        session_time
        + timedelta(hours=10)
    )

    past_dates = (
        datetime.now()
        > session_time
    )


    # ========================================================
    # SESSIONS TO LOAD
    # ========================================================

    s_no = sessions_year.loc[
        sessions_year["RaceID"] == race_id,
        "SessionNo"
    ].tolist()


    # Only load sessions which have happened
    session_dates = sessions_year.loc[
        sessions_year["RaceID"] == race_id
    ].copy()

    session_dates["HasHappened"] = (
        datetime.now()
        >
        (
            session_dates["SessionDateUtc"]
            + timedelta(hours=10)
        )
    )


    s_no = session_dates.loc[
        session_dates["HasHappened"],
        "SessionNo"
    ].tolist()


    # ========================================================
    # LOOP THROUGH SESSIONS
    # ========================================================

    for sess in s_no:

        # ----------------------------------------------------
        # SESSION ID
        # ----------------------------------------------------

        sessionnumber = (
            f"{race_id}-{sess}"
        )


        # ----------------------------------------------------
        # SESSION NAME
        # ----------------------------------------------------

        sessionname = sessions_year.loc[
            sessions_year["SessionID"] == sessionnumber,
            "SessionName"
        ].iloc[0]


        print(
            f"Loading {year} {event} {sessionname}..."
        )


        # ====================================================
        # LOAD SESSION
        # ====================================================

        session = fastf1.get_session(
            year,
            event,
            sess
        )

        session.load(laps=True,
                     telemetry=True,
                     weather=True,
                     messages=True)


        # ====================================================
        # CORNERS
        # ====================================================

        if sess == 1:  # Change this back to 1 later ---------------------------------
            try:
                corners = (
                    session
                    .get_circuit_info()
                    .corners
                    .copy()
                )
    
    
                # ------------------------------------------------
                # FOREIGN KEY
                # ------------------------------------------------
    
                corners["RaceID"] = race_id
    
                corners["RoundNumber"] = roundnumber
    
    
                # ------------------------------------------------
                # CORNER PRIMARY KEY
                #
                # CornerID = RaceID + Corner Number
                # ------------------------------------------------
    
                corners["CornerID"] = (
                    corners["RaceID"].astype(str)
                    + "-"
                    + corners["Number"].astype(str)
                )
    
    
                # ------------------------------------------------
                # FUEL TIME CALCULATIONS
                # ------------------------------------------------
    
                track_length = max(
                    session
                    .get_circuit_info()
                    .marshal_sectors["Distance"]
                )
    
                lap_count = round(
                    305000 / track_length
                )
    
                start_race_fuel = 110  # kg
    
                fuel_kg_per_lap = (
                    start_race_fuel
                    / lap_count
                )
    
                time_per_kg = 0.03
    
                time_gained_per_lap_run = round(
                    fuel_kg_per_lap
                    * time_per_kg,
                    3
                )
                
                circuitname = session.session_info['Meeting']['Circuit']['ShortName']
    
                # ------------------------------------------------
                # ADD RACE INFORMATION
                # ------------------------------------------------
    
                races_year["TrackLength"] = None
                races_year["No_of_Laps"] = None
                races_year[
                    "Time_Saved_per_Lap_Fuel"
                ] = None
                races_year['CircuitName'] = None
    
    
                races_year.loc[
                    races_year["RaceID"] == race_id,
                    "TrackLength"
                ] = track_length
    
    
                races_year.loc[
                    races_year["RaceID"] == race_id,
                    "No_of_Laps"
                ] = lap_count
    
    
                races_year.loc[
                    races_year["RaceID"] == race_id,
                    "Time_Saved_per_Lap_Fuel"
                ] = time_gained_per_lap_run
    
    
                races_year.loc[
                    races_year["RaceID"] == race_id,
                    "CircuitName"
                ] = circuitname
    
                # ------------------------------------------------
                # SAVE CORNERS
                # ------------------------------------------------
    
                all_corners.append(
                    corners
                )
            except (AttributeError, TypeError, NameError):
                print(f"⚠️ Circuit information unavailable for {session.event['EventName']}")
                
                # Create an empty DataFrame with the columns your SQL upload expects
                corners = pd.DataFrame(columns=['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance', 'RaceID',
                                   'CornerID']
                )


        # ====================================================
        # DRIVER / TEAM INFO
        # ====================================================

        drivers_session = (
            session
            ._drivers_from_f1_api()
        )


        all_driver_info.append(
            drivers_session.copy()
        )


        team_info_session = drivers_session[
            [
                "TeamName",
                "TeamColor"
            ]
        ].copy()


        all_team_info.append(
            team_info_session
        )


        # ====================================================
        # WEATHER
        # ====================================================

        weather_session = (
            session
            .weather_data
            .copy()
        )


        weather_session["SessionID"] = (
            sessionnumber
        )


        all_weather.append(
            weather_session
        )


        # ====================================================
        # LAPS
        # ====================================================

        laps_session = (
            session
            .laps
            .copy()
        )


        # ----------------------------------------------------
        # FOREIGN KEYS
        # ----------------------------------------------------

        laps_session["SessionID"] = (
            sessionnumber
        )

        laps_session["RaceID"] = (
            race_id
        )


        # ----------------------------------------------------
        # LAP TIME
        # ----------------------------------------------------

        laps_session["LapTimeSeconds"] = (
            laps_session["LapTime"]
            .dt.total_seconds()
        )


        # ----------------------------------------------------
        # LAP INTO STINT
        # ----------------------------------------------------

        laps_session["LapIntoStint"] = (
            laps_session
            .groupby(
                [
                    "DriverNumber",
                    "Stint"
                ]
            )["LapNumber"]
            .transform(
                lambda x:
                x - x.min() + 1
            )
        )

        """
        # ----------------------------------------------------
        # FILTER RUBBISH LAPS
        # ----------------------------------------------------

        team_fastest_lap = (
            laps_session
            .groupby("Team")[
                "LapTimeSeconds"
            ]
            .transform("min")
        )


        laps_session[
            "QuickLap_Binary"
        ] = (
            laps_session[
                "LapTimeSeconds"
            ].notna()
            &
            (
                laps_session[
                    "LapTimeSeconds"
                ]
                <=
                team_fastest_lap * 1.10
            )
        ).astype(int)
        """
        # ----------------------------------------------------
        # FILTER RUBBISH LAPS
        # ----------------------------------------------------
        
        laps_session = laps_session.sort_values(
            ["Team", "LapNumber"]
        ).copy()
        
        window = 5
        threshold = 1.10
        
        
        def local_fastest(series):
        
            previous = (
                series
                .rolling(
                    window=window,
                    min_periods=1
                )
                .min()
            )
        
            following = (
                series
                .iloc[::-1]
                .rolling(
                    window=window,
                    min_periods=1
                )
                .min()
                .iloc[::-1]
            )
        
            return pd.concat(
                [previous, following],
                axis=1
            ).min(axis=1)
        
        
        laps_session["LocalFastestLap"] = (
            laps_session
            .groupby("Team")["LapTimeSeconds"]
            .transform(local_fastest)
        )
        
        
        laps_session["QuickLap_Binary"] = (
            laps_session["LapTimeSeconds"].notna()
            &
            (
                laps_session["LapTimeSeconds"]
                <=
                laps_session["LocalFastestLap"] * threshold
            )
        ).astype(int)
        # ----------------------------------------------------
        # FUEL LOSS TIME
        # ----------------------------------------------------
        
        try:
            laps_session[
                "FuelAdjustedLapTime"
            ] = (
                laps_session[
                    "LapTimeSeconds"
                ]
                +
                (
                    laps_session[
                        "LapIntoStint"
                    ] - 1
                )
                * time_gained_per_lap_run
            )
                
        except (AttributeError, TypeError, NameError):
            laps_session["FuelAdjustedLapTime"] = None 
        
        all_laps.append(
            laps_session
        )


        # ====================================================
        # CAR DATA
        # ====================================================

        cardata = session.car_data


        for i in cardata:

            cardata[i] = (
                cardata[i]
                .add_distance()
            )


        telemetry_session = pd.concat(
            cardata.values(),
            keys=cardata.keys(),
            names=["DriverNumber"]
        ).reset_index(
            level="DriverNumber"
        )


        telemetry_session[
            "DriverNumber"
        ] = (
            telemetry_session[
                "DriverNumber"
            ].astype(str)
        )


        # ====================================================
        # MATCH TELEMETRY TO LAPS
        # ====================================================

        laps_merge = (
            laps_session[
                [
                    "DriverNumber",
                    "LapStartDate",
                    "LapNumber"
                ]
            ]
            .assign(
                DriverNumber=lambda x:
                x["DriverNumber"].astype(str)
            )
            .dropna(
                subset=["LapStartDate"]
            )
            .sort_values(
                [
                    "LapStartDate",
                    "DriverNumber"
                ]
            )
            .reset_index(drop=True)
        )


        telemetry_session = (
            telemetry_session
            .dropna(
                subset=["Date"]
            )
            .sort_values(
                [
                    "Date",
                    "DriverNumber"
                ]
            )
            .reset_index(drop=True)
        )


        telemetry_session = pd.merge_asof(
            telemetry_session,
            laps_merge,
            left_on="Date",
            right_on="LapStartDate",
            by="DriverNumber",
            direction="backward"
        )


        telemetry_session[
            "TimeThroughLap"
        ] = (
            telemetry_session["Date"]
            -
            telemetry_session["LapStartDate"]
        ).dt.total_seconds()


        # ====================================================
        # POSITION DATA
        # ====================================================

        posdata = pd.concat(
            session.pos_data.values(),
            keys=session.pos_data.keys(),
            names=["DriverNumber"]
        ).reset_index(
            level="DriverNumber"
        )


        posdata["DriverNumber"] = (
            posdata["DriverNumber"]
            .astype(str)
        )


        telemetry_session[
            "DriverNumber"
        ] = (
            telemetry_session[
                "DriverNumber"
            ].astype(str)
        )


        telemetry_session = (
            telemetry_session
            .sort_values("Date")
        )


        posdata = (
            posdata
            .sort_values("Date")
        )


        telemetry_session = pd.merge_asof(
            telemetry_session,
            posdata[
                [
                    "DriverNumber",
                    "Date",
                    "X",
                    "Y",
                    "Z"
                ]
            ],
            on="Date",
            by="DriverNumber",
            direction="nearest",
            tolerance=pd.Timedelta(
                milliseconds=200
            )
        )


        # ====================================================
        # SESSION START FILTER
        # ====================================================

        starttime = sessions_year.loc[
            sessions_year["SessionID"]
            == sessionnumber,
            "SessionDateUtc"
        ].iloc[0]


        telemetry_session = (
            telemetry_session[
                telemetry_session["Date"]
                > starttime
            ]
            .copy()
        )


        # ====================================================
        # SESSION FOREIGN KEYS
        # ====================================================

        telemetry_session[
            "SessionID"
        ] = sessionnumber

        telemetry_session[
            "RaceID"
        ] = race_id


        all_telemetry.append(
            telemetry_session
        )


    # ========================================================
    # UPDATE RACE INFORMATION IN MASTER LIST
    # ========================================================

    # The race row may have received track information
    # during the session loop, so replace the original copy.

    all_races[-1] = races_year.copy()


# ============================================================
# COMBINE RACES
# ============================================================

races = pd.concat(
    all_races,
    ignore_index=True
)


# ============================================================
# COMBINE SESSIONS
# ============================================================

sessions = pd.concat(
    all_sessions,
    ignore_index=True
)


# ============================================================
# COMBINE CORNERS
# ============================================================

if all_corners:
    corners = pd.concat(
        all_corners,
        ignore_index=True
    )

print(f"Corners: {len(corners)} rows")



# ============================================================
# CREATE DRIVER / TEAM TABLES
# ============================================================

driver_info = pd.concat(
    all_driver_info,
    ignore_index=True
)


# ============================================================
# DRIVERS
#
# Keep all driver information.
#
# Remove duplicates based on FullName BEFORE DriverID.
# ============================================================

drivers = (
    driver_info
    .drop(
        columns=[
            "TeamName",
            "TeamColor",
            "DriverNumber"
        ],
        errors="ignore"
    )
    .drop_duplicates(
        subset=["FullName"]
    )
    .reset_index(drop=True)
)


drivers["DriverID"] = range(
    1,
    len(drivers) + 1
)


# ============================================================
# TEAMS
#
# Remove duplicate teams BEFORE TeamID.
# ============================================================

team_info = pd.concat(
    all_team_info,
    ignore_index=True
)


teams = (
    driver_info[
        [
            "TeamName"
        ]
    ]
    .dropna()
    .drop_duplicates()
    .sort_values("TeamName")
    .reset_index(drop=True)
)


teams = teams.merge(
    team_info[
        [
            "TeamName",
            "TeamColor"
        ]
    ].drop_duplicates("TeamName"),
    on="TeamName",
    how="left"
)


teams = teams.rename(
    columns={
        "TeamName": "Team"
    }
)


teams["TeamID"] = range(
    1,
    len(teams) + 1
)


teams = teams[
    [
        "TeamID",
        "Team",
        "TeamColor"
    ]
]


# ============================================================
# WEATHER
# ============================================================

weather = pd.concat(
    all_weather,
    ignore_index=True
)


# ============================================================
# WEATHER INDEX WITHIN SESSION
# ============================================================

weather["IndexInSession"] = (
    weather
    .groupby("SessionID")
    .cumcount()
)


# ============================================================
# WEATHER PRIMARY KEY
#
# WeatherID = SessionID + IndexInSession
# ============================================================

weather["WeatherID"] = (
    weather["SessionID"].astype(str)
    + "-"
    + weather["IndexInSession"].astype(str)
)


# ============================================================
# LAPS
# ============================================================

laps = pd.concat(
    all_laps,
    ignore_index=True
)


laps["DriverNumber"] = (
    laps["DriverNumber"]
    .astype(str)
)


# ============================================================
# ADD RACE INFORMATION TO LAPS
# ============================================================

laps = laps.merge(
    sessions[
        [
            "SessionID",
            "RaceID",
            "RoundNumber"
        ]
    ],
    on="SessionID",
    how="left",
    suffixes=("", "_Session")
)


# ============================================================
# CREATE DRIVER ENTRIES
#
# One row =
# one driver + one session
#
# PRIMARY KEY:
# EntryID = SessionID + DriverID
# ============================================================

driver_entries = (
    laps[
        [
            "SessionID",
            "Driver",
            "DriverNumber",
            "Team"
        ]
    ]
    .dropna(
        subset=[
            "Driver",
            "Team",
            "SessionID"
        ]
    )
    .drop_duplicates()
)


# ============================================================
# MAP DRIVER → DRIVER ID
# ============================================================

driver_entries = driver_entries.merge(
    drivers[
        [
            "DriverID",
            "Abbreviation",
            "FullName"
        ]
    ],
    left_on="Driver",
    right_on="Abbreviation",
    how="left"
)


# ============================================================
# MAP TEAM → TEAM ID
# ============================================================

driver_entries = driver_entries.merge(
    teams[
        [
            "TeamID",
            "Team"
        ]
    ],
    on="Team",
    how="left"
)


# ============================================================
# CHECK FAILED MAPPINGS
# ============================================================

missing_driver_ids = (
    driver_entries["DriverID"]
    .isna()
    .sum()
)

missing_team_ids = (
    driver_entries["TeamID"]
    .isna()
    .sum()
)


if missing_driver_ids > 0:

    print(
        f"WARNING: {missing_driver_ids} "
        f"driver entries have no DriverID."
    )


if missing_team_ids > 0:

    print(
        f"WARNING: {missing_team_ids} "
        f"driver entries have no TeamID."
    )


# ============================================================
# CREATE ENTRY ID
#
# EntryID = SessionID + DriverID
# ============================================================

driver_entries = (
    driver_entries[
        [
            "DriverID",
            "TeamID",
            "SessionID",
            "DriverNumber"
        ]
    ]
    .drop_duplicates()
    .reset_index(drop=True)
)


driver_entries["EntryID"] = (
    driver_entries["SessionID"].astype(str)
    + "-"
    + driver_entries["DriverID"].astype(str)
)


# ============================================================
# FINAL DRIVER ENTRY COLUMN ORDER
# ============================================================

driver_entries = driver_entries[
    [
        "EntryID",
        "DriverID",
        "TeamID",
        "SessionID",
        "DriverNumber"
    ]
]


# ============================================================
# CONNECT LAPS → DRIVER ENTRIES
# ============================================================

laps = laps.merge(
    driver_entries[
        [
            "EntryID",
            "DriverID",
            "TeamID",
            "SessionID",
            "DriverNumber"
        ]
    ],
    on=[
        "SessionID",
        "DriverNumber"
    ],
    how="left",
    validate="many_to_one",
    suffixes=("", "_Entry")
)


# ============================================================
# CHECK LAP → ENTRY MATCHING
# ============================================================

unmatched_laps = (
    laps["EntryID"]
    .isna()
    .sum()
)


if unmatched_laps > 0:

    print(
        f"WARNING: {unmatched_laps} laps "
        f"could not be matched to Driver_Entries."
    )


# ============================================================
# CREATE LAP ID
#
# PRIMARY KEY:
# LapID = EntryID + LapNumber
# ============================================================

laps["LapID"] = (
    laps["EntryID"].astype(str)
    + "-"
    + laps["LapNumber"]
        .apply(
            lambda x:
            str(int(x))
            if pd.notna(x)
            else "NA"
        )
)


# ============================================================
# TELEMETRY
# ============================================================

telemetry = pd.concat(
    all_telemetry,
    ignore_index=True
)


telemetry["DriverNumber"] = (
    telemetry["DriverNumber"]
    .astype(str)
)


# ============================================================
# MATCH TELEMETRY → LAPS
# ============================================================

laps = laps.drop_duplicates(
    subset=["LapID"],
    keep="first"
).copy()

if laps["LapID"].duplicated().any():
    raise Exception(
        "Duplicate LapIDs still exist after deduplication."
    )

telemetry = telemetry.merge(
    laps[
        [
            "LapID",
            "SessionID",
            "DriverNumber",
            "LapNumber"
        ]
    ],
    on=[
        "SessionID",
        "DriverNumber",
        "LapNumber"
    ],
    how="left",
    validate="many_to_one"
)



telemetry["TelemetryID"] = (
    telemetry["SessionID"].astype(str)
    + "-"
    + telemetry.groupby("SessionID").cumcount().add(1).astype(str)
)

try:
    races = races[['RoundNumber', 'Country', 'Location', 'OfficialEventName', 'EventDate',
                    'EventName', 'EventFormat', 'F1ApiSupport', 'Year', 'RaceID', 
                    'TrackLength', 'No_of_Laps', 'Time_Saved_per_Lap_Fuel']]
except (KeyError):
    races = races[['RoundNumber', 'Country', 'Location', 'OfficialEventName', 'EventDate',
                    'EventName', 'EventFormat', 'F1ApiSupport', 'Year', 'RaceID']]

drivers = drivers[['BroadcastName', 'Abbreviation', 'FirstName', 'LastName', 'HeadshotUrl',
                   'FullName', 'DriverID']]

weather = weather[['Time', 'AirTemp', 'Humidity', 'Pressure', 'Rainfall', 'TrackTemp',
                   'WindDirection', 'WindSpeed', 'SessionID', 'WeatherID']]

sessions = sessions[['RaceID', 'SessionNo', 'SessionName', 'SessionDate',
                     'SessionDateUtc', 'SessionID']]

corners = corners[['X', 'Y', 'Number', 'Letter', 'Angle', 'Distance', 'RaceID',
                   'CornerID']]

laps = laps[['Time', 'LapNumber', 'Stint',
       'PitOutTime', 'PitInTime', 'Sector1Time', 'Sector2Time', 'Sector3Time',
       'Sector1SessionTime', 'Sector2SessionTime', 'Sector3SessionTime',
       'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 'IsPersonalBest',
       'Compound', 'TyreLife', 'FreshTyre', 'LapStartTime',
       'LapStartDate', 'TrackStatus', 'Position', 'Deleted', 'DeletedReason',
       'SessionID',
       'LapTimeSeconds', 'LapIntoStint', 'QuickLap_Binary',
       'FuelAdjustedLapTime', 'EntryID',
       'LapID']]

telemetry = telemetry[['Date', 'RPM', 'Speed', 'nGear', 'Throttle', 'Brake',
       'DRS', 'Source', 'Time', 'SessionTime', 'Distance', 'LapStartDate',
       'LapNumber', 'TimeThroughLap', 'X', 'Y', 'Z', 'SessionID',
       'LapID', 'TelemetryID']]

teams = teams[['TeamID', 'Team', 'TeamColor']]

driver_entries = driver_entries[['EntryID', 'DriverID', 'TeamID', 
                                 'SessionID', 'DriverNumber']]

end_time = time.time()

print(f"Total runtime: {end_time - start_time:.2f} seconds")

# ============================================================
# SEND DATA TO SQL SERVER
#
# Strategy:
#
#   Python DataFrame
#        ↓
#   Upload_* staging table
#        ↓
#   SQL Server compares staging vs permanent table
#        ↓
#   INSERT new rows
#        ↓
#   Races: UPDATE existing rows when calculated data exists
#        ↓
#   TRUNCATE staging table
#
# Existing data is NEVER downloaded into Python.
# ============================================================


if send_to_sql:

    import urllib.parse
    from sqlalchemy import create_engine, text


    # ========================================================
    # SQL CONNECTION
    # ========================================================

    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 13 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
    )

    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True
    )


    print("")
    print("=" * 70)
    print("UPLOADING DATA TO SQL DATABASE")
    print("=" * 70)


    # ========================================================
    # PREPARE DATA
    #
    # Only keep columns that belong in the SQL tables.
    # ========================================================
    try:
        races_sql = races[
            [
                "RoundNumber",
                "Country",
                "Location",
                "OfficialEventName",
                "EventDate",
                "EventName",
                "EventFormat",
                "F1ApiSupport",
                "Year",
                "RaceID",
                "TrackLength",
                "No_of_Laps",
                "Time_Saved_per_Lap_Fuel"
            ]
        ].copy()
    except (KeyError):
        races_sql = races[
            [
                "RoundNumber",
                "Country",
                "Location",
                "OfficialEventName",
                "EventDate",
                "EventName",
                "EventFormat",
                "F1ApiSupport",
                "Year",
                "RaceID"
            ]
        ].copy()


    drivers_sql = drivers[
        [
            "BroadcastName",
            "Abbreviation",
            "FirstName",
            "LastName",
            "HeadshotUrl",
            "FullName",
            "DriverID"
        ]
    ].copy()


    teams_sql = teams[
        [
            "TeamID",
            "Team",
            "TeamColor"
        ]
    ].copy()


    sessions_sql = sessions[
        [
            "RaceID",
            "SessionNo",
            "SessionName",
            "SessionDate",
            "SessionDateUtc",
            "SessionID"
        ]
    ].copy()


    corners_sql = corners[
        [
            "X",
            "Y",
            "Number",
            "Letter",
            "Angle",
            "Distance",
            "RaceID",
            "CornerID"
        ]
    ].copy()


    weather_sql = weather[
        [
            "Time",
            "AirTemp",
            "Humidity",
            "Pressure",
            "Rainfall",
            "TrackTemp",
            "WindDirection",
            "WindSpeed",
            "SessionID",
            "WeatherID"
        ]
    ].copy()


    driver_entries_sql = driver_entries[
        [
            "EntryID",
            "DriverID",
            "TeamID",
            "SessionID",
            "DriverNumber"
        ]
    ].copy()


    laps_sql = laps[
        [
            "Time",
            "LapNumber",
            "Stint",
            "PitOutTime",
            "PitInTime",
            "Sector1Time",
            "Sector2Time",
            "Sector3Time",
            "Sector1SessionTime",
            "Sector2SessionTime",
            "Sector3SessionTime",
            "SpeedI1",
            "SpeedI2",
            "SpeedFL",
            "SpeedST",
            "IsPersonalBest",
            "Compound",
            "TyreLife",
            "FreshTyre",
            "LapStartTime",
            "LapStartDate",
            "TrackStatus",
            "Position",
            "Deleted",
            "DeletedReason",
            "SessionID",
            "LapTimeSeconds",
            "LapIntoStint",
            "QuickLap_Binary",
            "FuelAdjustedLapTime",
            "EntryID",
            "LapID"
        ]
    ].copy()


    telemetry_sql = telemetry[
        [
            "Date",
            "RPM",
            "Speed",
            "nGear",
            "Throttle",
            "Brake",
            "DRS",
            "Source",
            "Time",
            "SessionTime",
            "Distance",
            "LapStartDate",
            "LapNumber",
            "TimeThroughLap",
            "X",
            "Y",
            "Z",
            "SessionID",
            "LapID",
            "TelemetryID"
        ]
    ].copy()


    # ========================================================
    # REMOVE DUPLICATES WITHIN THE PYTHON BATCH
    #
    # This prevents the same row appearing multiple times in
    # the staging table.
    # ========================================================

    races_sql = races_sql.drop_duplicates(
        subset=["RaceID"],
        keep="last"
    )


    drivers_sql = drivers_sql.drop_duplicates(
        subset=["FullName"],
        keep="last"
    )


    teams_sql = teams_sql.drop_duplicates(
        subset=["Team"],
        keep="last"
    )


    sessions_sql = sessions_sql.drop_duplicates(
        subset=["SessionID"],
        keep="last"
    )


    corners_sql = corners_sql.drop_duplicates(
        subset=["CornerID"],
        keep="last"
    )


    weather_sql = weather_sql.drop_duplicates(
        subset=["WeatherID"],
        keep="last"
    )


    driver_entries_sql = driver_entries_sql.drop_duplicates(
        subset=["EntryID"],
        keep="last"
    )


    laps_sql = laps_sql.drop_duplicates(
        subset=["LapID"],
        keep="last"
    )


    telemetry_sql = telemetry_sql.drop_duplicates(
        subset=["TelemetryID"],
        keep="last"
    )


    # ========================================================
    # IMPORTANT:
    #
    # Race duplicate handling
    #
    # If the same RaceID appears more than once in the Python
    # data, prefer the version which has calculated race
    # information.
    #
    # TrackLength is the important indicator.
    # ========================================================

    try:
        races_sql["_HasRaceCalculation"] = (
            races_sql["TrackLength"].notna()
        )
    except (KeyError):
        races_sql["_HasRaceCalculation"] = None

    races_sql = (
        races_sql
        .sort_values(
            "_HasRaceCalculation",
            ascending=True
        )
        .drop_duplicates(
            subset=["RaceID"],
            keep="last"
        )
        .drop(
            columns=["_HasRaceCalculation"]
        )
    )


    # ========================================================
    # CONVERT TIMEDELTAS
    # ========================================================

    if "Time" in weather_sql.columns:

        if pd.api.types.is_timedelta64_dtype(
            weather_sql["Time"]
        ):

            weather_sql["Time"] = (
                weather_sql["Time"]
                .dt.total_seconds()
            )


    lap_time_columns = [
        "Time",
        "PitOutTime",
        "PitInTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
        "Sector1SessionTime",
        "Sector2SessionTime",
        "Sector3SessionTime",
        "LapStartTime"
    ]


    for col in lap_time_columns:

        if col in laps_sql.columns:

            if pd.api.types.is_timedelta64_dtype(
                laps_sql[col]
            ):

                laps_sql[col] = (
                    laps_sql[col]
                    .dt.total_seconds()
                )


    telemetry_time_columns = [
        "Time",
        "SessionTime"
    ]


    for col in telemetry_time_columns:

        if col in telemetry_sql.columns:

            if pd.api.types.is_timedelta64_dtype(
                telemetry_sql[col]
            ):

                telemetry_sql[col] = (
                    telemetry_sql[col]
                    .dt.total_seconds()
                )


    # ========================================================
    # CONVERT IDS TO STRING
    #
    # SQL VARCHAR columns.
    # ========================================================

    string_columns = {

        "Upload_Races": [
            "RaceID"
        ],

        "Upload_Sessions": [
            "RaceID",
            "SessionID"
        ],

        "Upload_Corners": [
            "RaceID",
            "CornerID"
        ],

        "Upload_Weather": [
            "SessionID",
            "WeatherID"
        ],

        "Upload_Driver_Entries": [
            "EntryID",
            "SessionID"
        ],

        "Upload_Laps": [
            "EntryID",
            "SessionID",
            "LapID"
        ],

        "Upload_Telemetry": [
            "SessionID",
            "LapID",
            "TelemetryID"
        ],

        "Upload_Drivers": [
            "Abbreviation",
            "FullName"
        ],

        "Upload_Teams": [
            "Team"
        ]
    }


    dataframes = {

        "Upload_Races": races_sql,

        "Upload_Drivers": drivers_sql,

        "Upload_Teams": teams_sql,

        "Upload_Sessions": sessions_sql,

        "Upload_Corners": corners_sql,

        "Upload_Weather": weather_sql,

        "Upload_Driver_Entries": driver_entries_sql,

        "Upload_Laps": laps_sql,

        "Upload_Telemetry": telemetry_sql
    }


    for table_name, columns in string_columns.items():

        df = dataframes[table_name]

        for col in columns:

            if col in df.columns:

                df[col] = df[col].where(
                    df[col].notna(),
                    None
                )

                df[col] = df[col].astype(object)

                mask = df[col].notna()

                df.loc[mask, col] = (
                    df.loc[mask, col].astype(str)
                )


    # ========================================================
    # SQL UPLOAD HELPER
    # ========================================================

    def upload_staging(
        conn,
        df,
        staging_table
    ):

        if df.empty:

            print(
                f"{staging_table}: nothing to upload"
            )

            return 0


        # ----------------------------------------------------
        # Clear previous staging data
        # ----------------------------------------------------

        conn.execute(
            text(
                f"TRUNCATE TABLE {staging_table}"
            )
        )


        # ----------------------------------------------------
        # Upload batch
        # ----------------------------------------------------

        df.to_sql(
            staging_table.replace("Upload_", ""),
            conn,
            if_exists="append",
            index=False,
            chunksize=10000
        )

        return len(df)


    # ========================================================
    # BEGIN TRANSACTION
    # ========================================================

    with engine.begin() as conn:


        # ====================================================
        # 1. RACES
        #
        # Special behaviour:
        #
        # If RaceID doesn't exist:
        #     INSERT
        #
        # If RaceID exists:
        #     UPDATE calculated race information if incoming
        #     TrackLength is not NULL.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Races
            """)
        )


        if not races_sql.empty:

            races_sql.to_sql(
                "Upload_Races",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        race_result = conn.execute(
            text("""
                UPDATE R
                SET
                    R.Year = U.Year,
                    R.RoundNumber = U.RoundNumber,
                    R.EventName = U.EventName,
                    R.Country = U.Country,
                    R.Location = U.Location,
                    R.OfficialEventName = U.OfficialEventName,
                    R.EventDate = U.EventDate,
                    R.EventFormat = U.EventFormat,
                    R.F1ApiSupport = U.F1ApiSupport,

                    R.TrackLength = U.TrackLength,
                    R.No_of_Laps = U.No_of_Laps,
                    R.Time_Saved_per_Lap_Fuel =
                        U.Time_Saved_per_Lap_Fuel

                FROM Races R
                INNER JOIN Upload_Races U
                    ON R.RaceID = U.RaceID

                WHERE U.TrackLength IS NOT NULL
            """)
        )


        race_update_count = race_result.rowcount


        race_result = conn.execute(
            text("""
                INSERT INTO Races
                (
                    RaceID,
                    Year,
                    RoundNumber,
                    EventName,
                    Country,
                    Location,
                    OfficialEventName,
                    EventDate,
                    EventFormat,
                    F1ApiSupport,
                    TrackLength,
                    No_of_Laps,
                    Time_Saved_per_Lap_Fuel
                )

                SELECT
                    U.RaceID,
                    U.Year,
                    U.RoundNumber,
                    U.EventName,
                    U.Country,
                    U.Location,
                    U.OfficialEventName,
                    U.EventDate,
                    U.EventFormat,
                    U.F1ApiSupport,
                    U.TrackLength,
                    U.No_of_Laps,
                    U.Time_Saved_per_Lap_Fuel

                FROM Upload_Races U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Races R
                    WHERE R.RaceID = U.RaceID
                )
            """)
        )


        race_insert_count = race_result.rowcount


        print(
            f"Races:          "
            f"{race_insert_count:,} new, "
            f"{race_update_count:,} updated"
        )


        # ====================================================
        # 2. DRIVERS
        #
        # FullName is the natural key.
        #
        # SQL Server generates DriverID.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Drivers
            """)
        )


        if not drivers_sql.empty:

            drivers_sql[
                [
                    "BroadcastName",
                    "Abbreviation",
                    "FirstName",
                    "LastName",
                    "HeadshotUrl",
                    "FullName"
                ]
            ].to_sql(
                "Upload_Drivers",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        result = conn.execute(
            text("""
                INSERT INTO Drivers
                (
                    BroadcastName,
                    Abbreviation,
                    FirstName,
                    LastName,
                    HeadshotUrl,
                    FullName
                )

                SELECT
                    U.BroadcastName,
                    U.Abbreviation,
                    U.FirstName,
                    U.LastName,
                    U.HeadshotUrl,
                    U.FullName

                FROM Upload_Drivers U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Drivers D
                    WHERE D.FullName = U.FullName
                )
            """)
        )


        driver_count = result.rowcount


        print(
            f"Drivers:        {driver_count:,} new"
        )


        # ====================================================
        # 3. TEAMS
        #
        # Team is the natural key.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Teams
            """)
        )


        if not teams_sql.empty:

            teams_sql[
                [
                    "Team",
                    "TeamColor"
                ]
            ].to_sql(
                "Upload_Teams",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        result = conn.execute(
            text("""
                INSERT INTO Teams
                (
                    Team,
                    TeamColor
                )

                SELECT
                    U.Team,
                    U.TeamColor

                FROM Upload_Teams U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Teams T
                    WHERE T.Team = U.Team
                )
            """)
        )


        team_count = result.rowcount


        print(
            f"Teams:          {team_count:,} new"
        )


        # ====================================================
        # 4. SESSIONS
        #
        # SessionID is the PK.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Sessions
            """)
        )


        if not sessions_sql.empty:

            sessions_sql.to_sql(
                "Upload_Sessions",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        result = conn.execute(
            text("""
                INSERT INTO Sessions
                (
                    SessionID,
                    RaceID,
                    SessionNo,
                    SessionName,
                    SessionDate,
                    SessionDateUtc
                )

                SELECT
                    U.SessionID,
                    U.RaceID,
                    U.SessionNo,
                    U.SessionName,
                    U.SessionDate,
                    U.SessionDateUtc

                FROM Upload_Sessions U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Sessions S
                    WHERE S.SessionID = U.SessionID
                )
            """)
        )


        session_count = result.rowcount


        print(
            f"Sessions:       {session_count:,} new"
        )


        # ====================================================
        # 5. CORNERS
        #
        # CornerID is the PK.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Corners
            """)
        )


        if not corners_sql.empty:

            corners_sql.to_sql(
                "Upload_Corners",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        result = conn.execute(
            text("""
                INSERT INTO Corners
                (
                    CornerID,
                    RaceID,
                    X,
                    Y,
                    Number,
                    Letter,
                    Angle,
                    Distance
                )

                SELECT
                    U.CornerID,
                    U.RaceID,
                    U.X,
                    U.Y,
                    U.Number,
                    U.Letter,
                    U.Angle,
                    U.Distance

                FROM Upload_Corners U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Corners C
                    WHERE C.CornerID = U.CornerID
                )
            """)
        )


        corner_count = result.rowcount


        print(
            f"Corners:        {corner_count:,} new"
        )


        # ====================================================
        # 6. WEATHER
        #
        # WeatherID is the PK.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Weather
            """)
        )


        if not weather_sql.empty:

            weather_sql.to_sql(
                "Upload_Weather",
                conn,
                if_exists="append",
                index=False,
                chunksize=10000
            )


        result = conn.execute(
            text("""
                INSERT INTO Weather
                (
                    WeatherID,
                    SessionID,
                    Time,
                    AirTemp,
                    Humidity,
                    Pressure,
                    Rainfall,
                    TrackTemp,
                    WindDirection,
                    WindSpeed
                )

                SELECT
                    U.WeatherID,
                    U.SessionID,
                    U.Time,
                    U.AirTemp,
                    U.Humidity,
                    U.Pressure,
                    U.Rainfall,
                    U.TrackTemp,
                    U.WindDirection,
                    U.WindSpeed

                FROM Upload_Weather U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Weather W
                    WHERE W.WeatherID = U.WeatherID
                )
            """)
        )


        weather_count = result.rowcount


        print(
            f"Weather:        {weather_count:,} new"
        )


        # ====================================================
        # 7. DRIVER ENTRIES
        #
        # This is where we need to convert the Python IDs
        # into the actual SQL Server IDs.
        #
        # We match using:
        #
        # Python DriverID → Python drivers → FullName
        # FullName → SQL Drivers.DriverID
        #
        # Python TeamID → Python teams → Team
        # Team → SQL Teams.TeamID
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Driver_Entries
            """)
        )


        # ----------------------------------------------------
        # Build upload table with names rather than relying
        # on Python-generated identity IDs.
        # ----------------------------------------------------

        entry_upload = driver_entries_sql.copy()


        entry_upload = entry_upload.merge(
            drivers_sql[
                [
                    "DriverID",
                    "FullName"
                ]
            ],
            on="DriverID",
            how="left"
        )


        entry_upload = entry_upload.merge(
            teams_sql[
                [
                    "TeamID",
                    "Team"
                ]
            ],
            on="TeamID",
            how="left",
            suffixes=(
                "",
                "_Team"
            )
        )


        if (
            entry_upload["FullName"]
            .isna()
            .any()
        ):

            raise Exception(
                "Could not map one or more Python "
                "DriverIDs to FullName."
            )


        if (
            entry_upload["Team"]
            .isna()
            .any()
        ):

            raise Exception(
                "Could not map one or more Python "
                "TeamIDs to Team."
            )


        entry_upload[
            [
                "EntryID",
                "SessionID",
                "DriverNumber",
                "FullName",
                "Team"
            ]
        ].to_sql(
            "Upload_Driver_Entries",
            conn,
            if_exists="append",
            index=False,
            chunksize=10000
        )


        result = conn.execute(
            text("""
                INSERT INTO Driver_Entries
                (
                    EntryID,
                    DriverID,
                    TeamID,
                    SessionID,
                    DriverNumber
                )

                SELECT
                    U.EntryID,
                    D.DriverID,
                    T.TeamID,
                    U.SessionID,
                    U.DriverNumber

                FROM Upload_Driver_Entries U

                INNER JOIN Drivers D
                    ON D.FullName = U.FullName

                INNER JOIN Teams T
                    ON T.Team = U.Team

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Driver_Entries E
                    WHERE E.EntryID = U.EntryID
                )
            """)
        )


        entry_count = result.rowcount


        print(
            f"Driver Entries: {entry_count:,} new"
        )


        # ====================================================
        # 8. LAPS
        #
        # LapID is the PK.
        #
        # No existing Laps data is downloaded.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Laps
            """)
        )


        if not laps_sql.empty:

            laps_sql.to_sql(
                "Upload_Laps",
                conn,
                if_exists="append",
                index=False,
                chunksize=20000
            )


        result = conn.execute(
            text("""
                INSERT INTO Laps
                (
                    LapID,
                    EntryID,
                    SessionID,
                
                    Time,
                    LapNumber,
                    Stint,
                
                    PitOutTime,
                    PitInTime,
                
                    Sector1Time,
                    Sector2Time,
                    Sector3Time,
                
                    Sector1SessionTime,
                    Sector2SessionTime,
                    Sector3SessionTime,
                
                    SpeedI1,
                    SpeedI2,
                    SpeedFL,
                    SpeedST,
                
                    IsPersonalBest,
                
                    Compound,
                    TyreLife,
                    FreshTyre,
                
                    LapStartTime,
                    LapStartDate,
                
                    TrackStatus,
                    Position,
                
                    Deleted,
                    DeletedReason,
                
                    LapTimeSeconds,
                    LapIntoStint,
                    QuickLap_Binary,
                    FuelAdjustedLapTime
                )
                SELECT
                    U.LapID,
                    U.EntryID,
                    U.SessionID,
                
                    U.Time,
                    U.LapNumber,
                    U.Stint,
                
                    U.PitOutTime,
                    U.PitInTime,
                
                    U.Sector1Time,
                    U.Sector2Time,
                    U.Sector3Time,
                
                    U.Sector1SessionTime,
                    U.Sector2SessionTime,
                    U.Sector3SessionTime,
                
                    U.SpeedI1,
                    U.SpeedI2,
                    U.SpeedFL,
                    U.SpeedST,
                
                    U.IsPersonalBest,
                
                    U.Compound,
                    U.TyreLife,
                    U.FreshTyre,
                
                    U.LapStartTime,
                    U.LapStartDate,
                
                    U.TrackStatus,
                    U.Position,
                
                    U.Deleted,
                    U.DeletedReason,
                
                    U.LapTimeSeconds,
                    U.LapIntoStint,
                    U.QuickLap_Binary,
                    U.FuelAdjustedLapTime
                
                FROM Upload_Laps U
                
                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Laps L
                    WHERE L.LapID = U.LapID
                );

            """)
        )


        lap_count = result.rowcount


        print(
            f"Laps:           {lap_count:,} new"
        )


        # ====================================================
        # 9. TELEMETRY
        #
        # TelemetryID is the PK.
        #
        # LapID is allowed to be NULL.
        #
        # Therefore telemetry occurring before a lap begins
        # is perfectly valid.
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Telemetry
            """)
        )

        t0 = time.perf_counter()
        
        if not telemetry_sql.empty:
            
            telemetry_sql.to_sql(
                "Upload_Telemetry",
                conn,
                if_exists="append",
                index=False,
                chunksize=100000
            )
        
        t1 = time.perf_counter()

        result = conn.execute(
            text("""
                INSERT INTO Telemetry
                (
                    TelemetryID,
                    LapID,

                    Date,
                    RPM,
                    Speed,
                    nGear,
                    Throttle,
                    Brake,
                    DRS,
                    Source,

                    Time,
                    SessionTime,
                    Distance,

                    LapStartDate,
                    LapNumber,
                    TimeThroughLap,

                    X,
                    Y,
                    Z,

                    SessionID
                )

                SELECT
                    U.TelemetryID,
                    U.LapID,

                    U.Date,
                    U.RPM,
                    U.Speed,
                    U.nGear,
                    U.Throttle,
                    U.Brake,
                    U.DRS,
                    U.Source,

                    U.Time,
                    U.SessionTime,
                    U.Distance,

                    U.LapStartDate,
                    U.LapNumber,
                    U.TimeThroughLap,

                    U.X,
                    U.Y,
                    U.Z,

                    U.SessionID

                FROM Upload_Telemetry U

                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM Telemetry T
                    WHERE T.TelemetryID = U.TelemetryID
                )
            """)
        )
        
        t2 = time.perf_counter()

        print(f"Staging upload: {t1 - t0:.2f} seconds")
        print(f"SQL compare + insert: {t2 - t1:.2f} seconds")

        telemetry_count = result.rowcount


        print(
            f"Telemetry:      {telemetry_count:,} new"
        )


        # ====================================================
        # CLEAR STAGING TABLES
        # ====================================================

        conn.execute(
            text("""
                TRUNCATE TABLE Upload_Races;

                TRUNCATE TABLE Upload_Drivers;

                TRUNCATE TABLE Upload_Teams;

                TRUNCATE TABLE Upload_Sessions;

                TRUNCATE TABLE Upload_Corners;

                TRUNCATE TABLE Upload_Weather;

                TRUNCATE TABLE Upload_Driver_Entries;

                TRUNCATE TABLE Upload_Laps;

                TRUNCATE TABLE Upload_Telemetry;
            """)
        )


    # ========================================================
    # FINAL DATABASE COUNTS
    # ========================================================

    with engine.connect() as conn:

        race_total = conn.execute(
            text("SELECT COUNT(*) FROM Races")
        ).scalar()

        session_total = conn.execute(
            text("SELECT COUNT(*) FROM Sessions")
        ).scalar()

        driver_total = conn.execute(
            text("SELECT COUNT(*) FROM Drivers")
        ).scalar()

        team_total = conn.execute(
            text("SELECT COUNT(*) FROM Teams")
        ).scalar()

        entry_total = conn.execute(
            text("SELECT COUNT(*) FROM Driver_Entries")
        ).scalar()

        corner_total = conn.execute(
            text("SELECT COUNT(*) FROM Corners")
        ).scalar()

        weather_total = conn.execute(
            text("SELECT COUNT(*) FROM Weather")
        ).scalar()

        lap_total = conn.execute(
            text("SELECT COUNT(*) FROM Laps")
        ).scalar()

        telemetry_total = conn.execute(
            text("SELECT COUNT(*) FROM Telemetry")
        ).scalar()


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print("")
    print("=" * 70)
    print("SQL DATABASE UPDATE COMPLETE")
    print("=" * 70)

    print(
        f"Races:          "
        f"{race_insert_count:,} new, "
        f"{race_update_count:,} updated"
    )

    print(f"Drivers:        {driver_count:,} new")
    print(f"Teams:          {team_count:,} new")
    print(f"Sessions:       {session_count:,} new")
    print(f"Corners:        {corner_count:,} new")
    print(f"Weather:        {weather_count:,} new")
    print(f"Driver Entries: {entry_count:,} new")
    print(f"Laps:           {lap_count:,} new")
    print(f"Telemetry:      {telemetry_count:,} new")

    print("")
    print("TOTAL RECORDS NOW IN SQL:")

    print(f"Races:          {race_total:,}")
    print(f"Sessions:       {session_total:,}")
    print(f"Drivers:        {driver_total:,}")
    print(f"Teams:          {team_total:,}")
    print(f"Driver Entries: {entry_total:,}")
    print(f"Corners:        {corner_total:,}")
    print(f"Weather:        {weather_total:,}")
    print(f"Laps:           {lap_total:,}")
    print(f"Telemetry:      {telemetry_total:,}")

    print("=" * 70)


end_time = time.time()

print(f"Total runtime: {end_time - start_time:.2f} seconds")
    
    
