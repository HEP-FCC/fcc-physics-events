<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'full-sim';
$campaign = 'v04';
?>

<?php
$txt_file = file_get_contents(BASE_PATH . '/data/FCChh/FCCsim_v04.txt');

$lname = array('No', 'Dir', 'Nevents', 'Nfiles', 'Neos', 'Nbad', 'Size [GB]',
               'aleksa', 'azaborow', 'cneubuse', 'djamin', 'helsens',
               'jhrdinka', 'jkiesele', 'novaj', 'selvaggi', 'vavolkl');

$description = 'FCC-hh Full Simulation v0.4 in EDM4hep format.';
?>

<?php require(BASE_PATH . '/FCChh/page.php') ?>
