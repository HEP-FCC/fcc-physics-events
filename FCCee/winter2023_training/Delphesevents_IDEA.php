<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$campaign = 'winter2023-training';
$det = 'idea';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_training_IDEA.txt';
$description = 'Delphes FCCee Physics events winter2023 training production (IDEA Detector).';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
