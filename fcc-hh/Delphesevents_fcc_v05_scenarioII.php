<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'fcc-v05-scenario-ii';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v05_scenarioII.txt';
$description = 'Delphes FCC-hh Physics events v0.5 scenario II. in EDM4Hep format.';
$stack = '/cvmfs/sw.hsf.org/key4hep/releases/2023-06-05-fcchh/x86_64-centos7-gcc12.2.0-opt/key4hep-stack/2023-08-28-hsn6vj/setup.sh';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
