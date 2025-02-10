<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023';
$det = 'idea-heavierbp-100pc';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_IDEA_heavierBP_100pc.txt';
$description = 'Delphes FCCee Physics events winter2023 production (IDEA detector with heavier BP &mdash; 100pc).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
