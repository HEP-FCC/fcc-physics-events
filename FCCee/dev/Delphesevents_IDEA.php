<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$campaign = 'dev';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_dev_IDEA.txt';
$description = 'Delphes FCCee Physic events dev production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
