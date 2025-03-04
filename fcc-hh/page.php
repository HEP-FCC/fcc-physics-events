<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?php
      $title = '';
      if ($campaign === 'v03') {
        $title .= 'v0.3 | ';
      }
      if ($campaign === 'v03-ecal') {
        $title .= 'v0.3 ECal | ';
      }
      if ($campaign === 'v04') {
        $title .= 'v0.4 | ';
      }
      if ($campaign === 'fcc-v02') {
        $title .= 'v0.2 | ';
      }
      if ($campaign === 'fcc-v03') {
        $title .= 'v0.3 | ';
      }
      if ($campaign === 'fcc-v04') {
        $title .= 'v0.4 | ';
      }
      if ($campaign === 'fcc-v05-scenario-i') {
        $title .= 'v0.5 scenario I. | ';
      }
      if ($campaign === 'fcc-v05-scenario-ii') {
        $title .= 'v0.5 scenario II. | ';
      }
      if ($campaign === 'fcc-v06') {
        $title .= 'v0.6 | ';
      }
      if ($fileType === 'lhe') {
        $title .= 'Les Houches | ';
      }

      if ($evtType === 'delphes') {
        $title .= 'Delphes | ';
      }
      if ($evtType === 'gen') {
        $title .= 'Gen | ';
      }
      if ($evtType === 'full-sim') {
        $title .= 'Full Sim | ';
      }

      $title .= 'FCC-hh | FCC Physics Events';

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
        $title = 'FCC-hh';

        if ($evtType === 'delphes') {
          $title .= ' | Delphes';
        }
        if ($evtType === 'gen') {
          $title .= ' | Gen';
        }
        if ($evtType === 'full-sim') {
          $title .= ' | Full Sim';
        }

        if ($campaign === 'v03') {
          $title .= ' | v0.3';
        }
        if ($campaign === 'v03-ecal') {
          $title .= ' | v0.3 ECal';
        }
        if ($campaign === 'v04') {
          $title .= ' | v0.4';
        }
        if ($campaign === 'fcc-v02') {
          $title .= ' | v0.2';
        }
        if ($campaign === 'fcc-v03') {
          $title .= ' | v0.3';
        }
        if ($campaign === 'fcc-v04') {
          $title .= ' | v0.4';
        }
        if ($campaign === 'fcc-v05-scenario-i') {
          $title .= ' | v0.5 scenario I.';
        }
        if ($campaign === 'fcc-v05-scenario-ii') {
          $title .= ' | v0.5 scenario II.';
        }
        if ($campaign === 'fcc-v06') {
          $title .= ' | v0.6';
        }
        if ($fileType === 'lhe') {
          $title .= ' | Les Houches';
        }

        $title .= ' Samples';

        echo $title;
      ?></h1>

      <p class="mt-3">
        <em><?= $description ?></em>
      </p>

      <?php if (isset($stack)): ?>
      <p>
        In the campaign the following
        <a href="https://cern.ch/key4hep/"
           target="_blank">Key4hep</a>&nbsp;<i class="bi bi-box-arrow-up-right"
                                              style="font-size: 12px; color: darkred;"></i>
        stack has been used:
        <pre>
          <code>
            <?= $stack ?>
          </code>
        </pre>
      </p>
      <?php endif ?>

      <p class="mt-3">
        <?php
          $statUrl = BASE_URL . '/data/FCChh/stat';

          if ($fileType === 'lhe') {
            $statUrl .= 'lhe';
          }

          if ($evtType === 'delphes') {
            $statUrl .= 'delphesfcc';
            $statUrl .= '_';
            $statUrl .= str_replace('-', '_', $campaign);
          }

          if ($evtType === 'full-sim') {
            $statUrl .= 'simu';
          }

          $statUrl .= '.html';
        ?>
        Additional stats about the production can be found <a href="<?= $statUrl ?>">here</a>.
      </p>

      <?php include BASE_PATH . '/includes/table-event-producer.php'; ?>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
