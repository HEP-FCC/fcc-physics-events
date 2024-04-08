<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'full-sim';
$campaign = 'v03';
?>

<?php
$txt_file = file_get_contents(BASE_PATH . '/data/FCChh/FCCsim_v03.txt');

$lname = array('No', 'Dir', 'Nevents', 'Nfiles', 'Neos', 'Nbad', 'Size [GB]',
               'aleksa', 'azaborow', 'cneubuse', 'djamin', 'helsens',
               'jhrdinka', 'jkiesele', 'novaj', 'selvaggi', 'vavolkl');

$description = 'FCC-hh Full Simulation v0.3.';
?>

<?php require(BASE_PATH . '/FCChh/page.php') ?>
