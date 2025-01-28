<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023-training';
$det = 'idea-worse-singlehitreso-100pc-heaviervtxlow-100pc';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_training_IDEA_worse_singlehitReso_100pc_heavierVTXLOW_100pc.txt';
$description = 'Delphes FCCee Physics events winter2023 training production (IDEA detector with worse single hit resolution &mdash; 100pc and heavier VTXLOW &mdash; 100pc).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
