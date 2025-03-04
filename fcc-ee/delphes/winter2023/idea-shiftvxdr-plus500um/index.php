<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023';
$det = 'idea-shiftvxdr-plus500um';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_IDEA_shiftVXDr_plus500um.txt';
$description = 'Delphes FCCee Physics events winter2023 production (IDEA detector with shifted VXD &mdash; r + 500um).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
