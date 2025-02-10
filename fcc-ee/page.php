<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?php
      $title = '';
      if (array_key_exists($det, $detectorNames)) {
        $title .= $detectorNames[$det] . ' | ';
      }

      if (array_key_exists($campaign, $campaignNames)) {
        $title .= $campaignNames[$campaign] . ' | ';
      }

      if ($fileType === 'stdhep') {
        $title .= 'STDHEP | ';
      }
      if ($fileType === 'lhe') {
        $title .= 'Les Houches | ';
      }

      if ($evtType === 'gen') {
        $title .= 'Gen | ';
      }
      if ($evtType === 'delphes') {
        $title .= 'Delphes | ';
      }
      if ($evtType === 'full-sim') {
        $title .= 'Full Sim | ';
      }

      $title .= 'FCC-ee | FCC Physics Events';

      echo $title;
    ?></title>

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

    <article id="sample-article" class="container-lg">
      <h1 class="mt-5"><?php
        $title = 'FCC-ee';

        if ($evtType === 'gen') {
          $title .= ' | Gen';
        }
        if ($evtType === 'delphes') {
          $title .= ' | Delphes';
        }
        if ($evtType === 'full-sim') {
          $title .= ' | Full Sim';
        }

        if ($fileType === 'stdhep') {
          $title .= ' | STDHEP';
        }
        if ($fileType === 'lhe') {
          $title .= ' | Les Houches';
        }

        if (array_key_exists($campaign, $campaignNames)) {
          $title .= ' | ' . $campaignNames[$campaign];
        }

        if (array_key_exists($det, $detectorNames)) {
          $title .= ' | ' . $detectorNames[$det];
        }

        $title .= ' Samples';

        echo $title;
      ?></h1>

      <p class="mt-3">
        <em><?= $description ?></em>
      </p>

      <?php if ($evtType === 'delphes' || $fileType === 'stdhep'): ?>
      <p class="mt-5">
        <a href="https://cern.ch/key4hep/">Key4hep</a> stack used during the generation of the
        <code><?= $campaignTags[$campaign] ?></code> samples was:
        <pre><code><?= $key4hepStacks[$campaign] ?></code></pre>
      </p>
      <?php endif ?>

      <p class="mt-3">
        <?php
          $prodStatUrl = $statUrl;
          if (!isset($statUrl)) {
            $statUrl = BASE_URL.'/data/FCCee/stat';

            if ($fileType === 'lhe') {
              $statUrl .= 'lhe';
            }

            if ($fileType === 'stdhep') {
              $statUrl .= '_stdhep_';
            }

            if ($evtType === 'delphes') {
              $statUrl .= 'delphes';
            }

            if (array_key_exists($campaign, $campaignTags)) {
              $statUrl .= $campaignTags[$campaign];
            }

            if (array_key_exists($det, $detectorNames)) {
              $statUrl .= '_' . str_replace(' ', '_', $detectorNames[$det]);
            }

            $statUrl .= '.html';
            $prodStatUrl = $statUrl;
          }
        ?>
        Additional stats about the production can be found <a href="<?= $prodStatUrl ?>">here</a>.
      </p>

      <?php include BASE_PATH . '/includes/table-event-producer.php'; ?>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
