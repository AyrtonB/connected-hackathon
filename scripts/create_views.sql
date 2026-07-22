-- Views for the Thames river network
-- Target: MET_SCRATCH.THAMES
-- Depends on: RIVER_LINKS table being populated

USE DATABASE MET_SCRATCH;
USE SCHEMA THAMES;

-- Simple name-based filter for Thames links
CREATE OR REPLACE VIEW RIVER_THAMES AS
SELECT *
FROM RIVER_LINKS
WHERE WATERCOURSE_NAME = 'River Thames'
   OR WATERCOURSE_NAME_ALTERNATIVE = 'River Thames';

-- Connected Thames: recursively bridges unnamed short links (<=1000m) that close
-- lock/weir/tidal gaps without pulling in named tributaries.
CREATE OR REPLACE VIEW RIVER_THAMES_CONNECTED AS
WITH RECURSIVE named_links AS (
    SELECT ID, START_NODE, END_NODE
    FROM RIVER_LINKS
    WHERE WATERCOURSE_NAME = 'River Thames'
       OR WATERCOURSE_NAME_ALTERNATIVE = 'River Thames'
),
all_named_nodes AS (
    SELECT START_NODE AS NODE FROM named_links
    UNION
    SELECT END_NODE AS NODE FROM named_links
),
bridging(ID, START_NODE, END_NODE) AS (
    -- Base case: unnamed short links touching a named Thames node
    SELECT rl.ID, rl.START_NODE, rl.END_NODE
    FROM RIVER_LINKS rl
    WHERE rl.WATERCOURSE_NAME IS NULL
      AND rl.WATERCOURSE_NAME_ALTERNATIVE IS NULL
      AND rl.LENGTH <= 1000
      AND (
          rl.START_NODE IN (SELECT NODE FROM all_named_nodes)
          OR rl.END_NODE IN (SELECT NODE FROM all_named_nodes)
      )

    UNION ALL

    -- Recursive step: unnamed short links touching an already-bridged node
    SELECT rl.ID, rl.START_NODE, rl.END_NODE
    FROM RIVER_LINKS rl
    JOIN bridging b
      ON rl.START_NODE IN (b.START_NODE, b.END_NODE)
      OR rl.END_NODE IN (b.START_NODE, b.END_NODE)
    WHERE rl.WATERCOURSE_NAME IS NULL
      AND rl.WATERCOURSE_NAME_ALTERNATIVE IS NULL
      AND rl.LENGTH <= 1000
      AND rl.ID != b.ID
)
SELECT rl.*
FROM RIVER_LINKS rl
WHERE rl.ID IN (SELECT ID FROM named_links)
   OR rl.ID IN (SELECT ID FROM bridging);
