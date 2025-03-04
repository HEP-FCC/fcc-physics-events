<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'spring2021';
$det = 'idea-fullsilicone';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_spring2021_IDEA_FullSilicon.txt';
$descrition = 'Delphes FCCee Physic events spring 2021 production (IDEA with Track Covariance full matrix lower triangle)';
$statUrl = '/data/FCCee/statdelphesspring2021_IDEA_FullSilicon.html';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
