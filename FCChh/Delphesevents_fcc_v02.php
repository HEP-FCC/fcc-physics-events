<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$campaign = 'v02';
?>

<?php
$txt_file = file_get_contents(BASE_PATH . '/data/FCChh/Delphesevents_fcc_v02.txt');

$lname = array('No', 'Name', 'Nevents', 'Nweights', 'Nfiles', 'Nbad', 'Neos',
               'Size [GB]', 'Output Path', 'Main Process', 'Final States',
               'Cross Section [pb]', 'K-factor', 'Matching Eff.');

$description = 'Delphes FCC-hh Physics events v0.2.';
?>

<?php require(BASE_PATH . '/FCChh/page.php') ?>
