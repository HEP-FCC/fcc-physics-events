<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023';
$det = 'idea-better-tofreso-3ps';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_IDEA_better_TOFReso_3ps.txt';
$description = 'Delphes FCCee Physics events winter2023 production (IDEA detector with better TOF resolution &mdash; 3ps).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
