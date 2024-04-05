<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea-3t';
$evtType = 'delphes';
$campaign = 'spring2021';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_spring2021_IDEA_3T.txt';
$description = 'Delphes FCCee Physics events Spring 2021 production (IDEA with Track Covariance full matrix lower triangle and 3T magnetic field).';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
