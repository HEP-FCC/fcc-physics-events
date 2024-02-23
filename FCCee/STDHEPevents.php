<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'none';
$evtType = 'stdhep';
$campaign = 'none';
?>

<?php
$txt_file    = file_get_contents('../data/FCCee/STDHEPevents.txt');

$lname=array('#','Name','Nevents',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Matching Param','Cross Section (pb)');

$description = '';
?>

<?php require(BASE_PATH . '/FCCee/page.php') ?>
