<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'spring2021-training';
$det = 'idea';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_spring2021_training_IDEA.txt';
$description = 'Delphes FCCee Physic events Spring 2021 &ndash; training  production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
