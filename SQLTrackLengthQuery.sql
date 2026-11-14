UPDATE Races
SET 
    TrackLength = 5891,
    No_of_Laps = ROUND(305000 / 5891, 0),
    Time_Saved_per_Lap_Fuel = ROUND(110 * 0.03 / ROUND(305000 / 5891, 0), 3)
WHERE RaceID = '2026-9'
  AND TrackLength IS NULL;