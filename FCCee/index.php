<?php
require('../config.php');

$layer = 'evt-type';
$acc = 'fcc-ee';
$det = 'none';
$evtType = 'none';
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
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include '../header.php'; ?>

    <article class="container-lg">
      <h1 class="mt-5">FCC-ee Samples</h1>

      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/LHEevents.php">Les Houches</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/stdhep/index.php">STDHEP</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/winter2023/index.php">Delphes | Winter 2023</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/winter2023_training/index.php">Delphes | Winter 2023 &ndash; training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/pre_fall2022/index.php">Delphes | Pre-fall 2022</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/pre_fall2022_training/index.php">Delphes | Pre-fall 2022 &ndash; training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/spring2021/index.php">Delphes | Spring 2021</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/spring2021_training/index.php">Delphes | Spring 2021 &ndash; training</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/dev/index.php">Delphes | Dev</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/FCCee/full-sim/index.php">Full Sim</a>
      </div>
      <h2 class="mt-5">Key4hep Stack</h2>

      <p>
        Exact <a href="https://cern.ch/key4hep/">Key4hep</a> stack used at the time of generation of the sample from the particular campaign can be found in the list below:
      </p>

      <ul>
        <li>
          <code>winter2023</code>
          <ul>
            <li>
              <code><?= $key4hepStacks['winter2023'] ?></code>
            </li>
          </ul>
        </li>
        <li>
          <code>winter2023_training</code>
          <ul>
            <li>
              <code><?= $key4hepStacks['winter2023-training'] ?></code>
            </li>
          </ul>
        </li>
        <li>
          <code>spring2021</code>
          <ul>
            <li>
              <code><?= $key4hepStacks['spring2021'] ?></code>
            </li>
          </ul>
        </li>
        <li>
          <code>spring2021_training</code>
          <ul>
            <li>
              <code><?= $key4hepStacks['spring2021-training'] ?></code>
            </li>
          </ul>
        </li>
      </ul>
    </article>

    <?php include '../footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
