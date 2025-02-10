<?php
require('../config.php');

$layer = 'evt-type';
$acc = 'fcc-ee';
$evtType = 'none';
$fileType = 'none';
$campaign = 'none';
$det = 'none';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FCC-ee | FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include BASE_PATH . '/header.php'; ?>

    <article class="container-lg">
      <h1 class="mt-5">FCC-ee Samples</h1>

      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/les-houches">Gen | Les Houches</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep">Gen | STDHEP</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023">Delphes | Winter 2023</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023-training">Delphes | Winter 2023&ndash;training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022">Delphes | Pre-fall 2022</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022-training">Delphes | Pre-fall 2022&ndash;training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021">Delphes | Spring 2021</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021-training">Delphes | Spring 2021&ndash;training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/dev">Delphes | Dev</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/full-sim">Full Sim</a>
      </div>

      <?php include BASE_PATH . '/includes/k4h-stack.php'; ?>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
