<?php
$config_array = parse_ini_file(__DIR__ . '/config.ini', true);

//
// Basics
//

define('BASE_URL', $config_array['basics']['BASE_URL']);
define('BASE_PATH',
       $_SERVER['DOCUMENT_ROOT'] . $config_array['basics']['BASE_PATH']);
define('SAMPLEDB_PATH',
       $_SERVER['DOCUMENT_ROOT'] . $config_array['basics']['SAMPLEDB_PATH']);

// Key4hep stacks
$key4hepStacks = $config_array['stacks']['key4hepStacks'];

// Detectors
$detectorNames = $config_array['detectors']['detectorNames'];
$campaignDetectors = $config_array['campaignDetectors'];
?>
