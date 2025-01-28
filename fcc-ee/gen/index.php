<?php
require('../../config.php');

$layer = 'gen-type';
$acc = 'fcc-ee';
$evtType = 'gen';
$fileType = 'none';
$campaign = 'none';
$det = 'none';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Gen | FCC-ee | FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include BASE_PATH . '/header.php'; ?>

    <article class="container-lg">
      <h1 class="mt-5">FCC-ee | Gen Samples</h1>

      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/les-houches">Les Houches</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/winter2023">STDHEP | Winter 2023</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/winter2023_training">STDHEP | Winter 2023&ndash;training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/spring2021">STDHEP | Spring 2021</a>
      </div>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>	
