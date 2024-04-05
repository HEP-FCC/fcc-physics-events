<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea-fullsilicon';
$evtType = 'delphes';
$campaign = 'spring2021';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_spring2021_IDEA_FullSilicon.txt';
$descrition = 'Delphes FCCee Physic events spring 2021 production (IDEA with Track Covariance full matrix lower triangle)';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
