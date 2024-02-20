<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea-3t';
$evtType = 'delphes';
$prodTag = 'spring2021';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_spring2021_IDEA_3T.txt');
$rows        = explode("\n", $txt_file);

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$NbrCol 	= count($lname); // $NbrCol : le nombre de colonnes

foreach($rows as $row => $data)
  {
    //get row data
    $row_data = explode(',,', $data);

    for ($i=0; $i<$NbrCol-1; $i++)
      {
        $info[$row][$lname[$i+1]] = $row_data[$i]; 
      }
  }

$NbrLigne 	= count($info);  // $NbrLigne : le nombre de lignes
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>IDEA 3T | Delphes | Spring 2021 | FCC-ee | FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include '../../header.php'; ?>

    <article id="sample-article" class="container-lg">
      <h1 class="mt-5">FCC-ee | Spring 2021 | Delphes | IDEA 3T Samples</h1>

      <p class="mt-3">
	<em>Delphes FCCee Physics events Spring 2021 production (IDEA with Track Covariance full matrix lower triangle and 3T magnetic field).</em>
      </p>

      <?php include 'stack.php'; ?>

      <p class="mt-5">
        Additional stats about the production can be found <a href="<?= BASE_URL ?>/data/FCCee/statdelphesspring2021_IDEA_3T.html">here</a>.
      </p>

      <?php include '../../table.php'; ?>
    </article>

    <?php include '../../footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
	    integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
