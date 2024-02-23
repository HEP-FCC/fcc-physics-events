<?php
require('../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'stdhep';
$campaign = 'winter2023';
$det = 'none';
?>

<?php
$txt_file = file_get_contents(BASE_PATH . '/data/FCCee/STDHEP_events_winter2023.txt');

$lname=array('#','Name','Nevents',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Matching Param','Cross Section (pb)');

$description = '';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
