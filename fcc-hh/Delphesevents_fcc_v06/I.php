<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'fcc-v06';
$det = 'i';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v06_I.txt';
$description = 'Delphes FCC-hh Physics events v0.6 scenario I. in EDM4Hep format.';
$stack = '/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
