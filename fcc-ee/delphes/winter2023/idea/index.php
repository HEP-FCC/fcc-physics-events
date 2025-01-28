<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023';
$det = 'idea';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_IDEA.txt';
$description = 'Delphes FCCee Physics events winter2023 production (IDEA Detector).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
