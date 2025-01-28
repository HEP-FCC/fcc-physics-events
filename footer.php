    <footer class="navbar bg-body-tertiary">
      <div class="mt-3 container-lg">
        <div class="container-lg">
          <div class="float-start">
            <a class="text-decoration-none"
               href="#"
               data-bs-toggle="modal"
               data-bs-target="#contactModal">Contact</a>
          </div>
          <div class="float-end">
            <a class="text-decoration-none"
               href="https://github.com/HEP-FCC/fcc-physics-events">Github</a>
          </div>
        </div>

        <div class="mt-3 container-lg text-center">
          <p class="text-body-secondary">
            &copy; Copyright 2024, CERN.
          </p>
        </div>
      </div>
    </footer>

    <div class="modal fade"
         id="aboutModal"
         tabindex="-1"
         aria-labelledby="aboutModalLabel"
         aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5" id="aboutModalLabel">About</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>
              This page lists all available pre-generated FCC samples and is
              automatically updated to include updates to existing samples or
              to list new ones. The propagation time for the updates is
              roughly &#189; day.
            </p>

            <p>
              In case of questions or any problems you can contact us through
              CERN e-group:
              <a href="mailto:FCC-PED-SoftwareAndComputing-Analysis@cern.ch"
                 target="_blank">FCC-PED-SoftwareAndComputing-Analysis</a>.
            </p>

            <hr>

            <p>
              Samples published on this site can have different statuses
              attached to them:
              <ul>
                <li>
                  <div class="bg-top-stopped"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> Stopped
                </li>
                <li>
                  <div class="bg-top-done"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> Done producing
                </li>
                <li>
                  <div class="bg-top-active"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> In active production
                </li>
                <li>
                  <div class="bg-top-not-registered"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> Not yet registered sample
                </li>
                <li>
                  <div class="bg-top-on-tape"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> Sample has been moved to tape
                </li>
                <li>
                  <div class="bg-top-unknown"
                       style="width: 20px; height: 20px; display: inline-block; vertical-align: middle;"></div> Sample with unknown status
                </li>
              </ul>
            <hr>

            <p>
              These pages were originaly created by Clement Helsens.
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade"
         id="contactModal"
         tabindex="-1"
         aria-labelledby="contactModalLabel"
         aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5" id="contactModalLabel">Contact</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            In case of questions or any problems you can contact us through CERN
            e-group:
            <a href="mailto:FCC-PED-SoftwareAndComputing-Analysis@cern.ch"
               target="_blank">FCC-PED-SoftwareAndComputing-Analysis</a>.
          </div>
          <div class="modal-footer">
            <button type="button"
                    class="btn btn-secondary"
                    data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
