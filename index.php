<?php
ini_set('display_errors', '1');
error_reporting(E_ALL);
$debug=(isset($_GET["debug"])?$_GET["debug"]:false);
if(!isset($gobase)){$gobase="";}

require('config.php');

$layer = 'top';
$acc = 'none';
$detector = 'none';
$evtType = 'none';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body data-bs-theme="light">
    <?php include 'header.php'; ?>

    <article class="container-lg mt-5">
      <h1>FCC Physics Events</h1>
      <p>Database of pre-generated samples for FCC-hh and <a href="https://hep-fcc.github.io/FCCeePhysicsPerformance/">FCC-ee physics performance studies</a>.</p>

      <h2>Accelerators</h2>
      The FCC integrated program includes two accelerator proposals:
      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/index.php">FCC-ee</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCChh/index.php">FCC-hh</a>
      </div>
    </article>

    <?php include 'footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>	
