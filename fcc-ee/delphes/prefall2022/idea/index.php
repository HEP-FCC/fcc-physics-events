<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'prefall2022';
$det = 'idea';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_pre_fall2022_IDEA.txt';
$description = 'Delphes FCCee Physics events pre-fall 2022 production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
