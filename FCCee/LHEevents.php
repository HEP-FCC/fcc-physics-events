<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'none';
$evtType = 'lhe';
$prodTag = 'none';
?>

<?php
$txt_file    = file_get_contents('../data/FCCee/LHEevents.txt');

$lname=array('#','Name','Nevents',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Matching Param','Cross Section (pb)');

$description = '';
?>

<?php require('page.php') ?>
