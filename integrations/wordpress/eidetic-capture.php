<?php
/**
 * Plugin Name:       Eidetic Capture
 * Plugin URI:        https://eidetic.works/wordpress
 * Description:       Captures published WordPress posts, pages, and custom post types as engrams in your local eideticd, so your AI sessions and writing live in one searchable store.
 * Version:           0.0.1
 * Requires at least: 5.0
 * Requires PHP:      7.4
 * Author:            Eidetic Works
 * Author URI:        https://eidetic.works
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       eidetic-capture
 */

// Exit if accessed directly.
if (!defined('ABSPATH')) {
    exit;
}

define('EIDETIC_CAPTURE_VERSION', '0.0.1');
define('EIDETIC_CAPTURE_DEFAULT_URL', 'http://127.0.0.1:8421');
define('EIDETIC_CAPTURE_OPTION', 'eidetic_capture_settings');
define('EIDETIC_CAPTURE_TIMEOUT', 5); // seconds — never block save_post

/**
 * Read plugin settings with defaults applied.
 *
 * @return array{daemon_url:string, token:string, published_only:bool}
 */
function eidetic_capture_get_settings() {
    $defaults = array(
        'daemon_url'     => EIDETIC_CAPTURE_DEFAULT_URL,
        'token'          => '',
        'published_only' => true,
    );
    $stored = get_option(EIDETIC_CAPTURE_OPTION, array());
    if (!is_array($stored)) {
        $stored = array();
    }
    $merged = array_merge($defaults, $stored);
    $merged['daemon_url']     = untrailingslashit(esc_url_raw($merged['daemon_url']));
    $merged['token']          = (string) $merged['token'];
    $merged['published_only'] = (bool) $merged['published_only'];
    return $merged;
}

/**
 * The save_post hook — fires on every post create/update.
 * We filter aggressively: skip auto-drafts, revisions, autosaves, and (by default) anything not yet published.
 */
function eidetic_capture_on_save_post($post_id, $post, $update) {
    // Operator escape-hatch for staging/dev sites.
    if (defined('EIDETIC_DISABLED') && EIDETIC_DISABLED) {
        return;
    }

    // Ignore autosaves + revisions — we only want intentional saves.
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id)) {
        return;
    }
    if (!($post instanceof WP_Post)) {
        return;
    }

    // WP creates an auto-draft on every "Add New" page-load — skip those.
    if (in_array($post->post_status, array('auto-draft', 'inherit', 'trash'), true)) {
        return;
    }

    $settings = eidetic_capture_get_settings();

    // Default posture: only publish events go to the daemon.
    if ($settings['published_only'] && $post->post_status !== 'publish') {
        return;
    }

    // Daemon URL must be set; token is recommended but not required (daemon may run open on localhost).
    if (empty($settings['daemon_url'])) {
        return;
    }

    $engram = array(
        'surface' => 'wordpress',
        'ts'      => gmdate('c'),
        'payload' => array(
            'post_id'     => (int) $post_id,
            'post_type'   => (string) $post->post_type,
            'post_status' => (string) $post->post_status,
            'title'       => (string) $post->post_title,
            'content'     => wp_strip_all_tags((string) $post->post_content),
            'permalink'   => (string) get_permalink($post),
        ),
        'meta' => array(
            'site_url'   => home_url(),
            'plugin'     => 'eidetic-capture',
            'plugin_ver' => EIDETIC_CAPTURE_VERSION,
            'author_id'  => (int) $post->post_author,
            'update'     => (bool) $update,
        ),
    );

    eidetic_capture_post_engram($settings, $engram);
}
add_action('save_post', 'eidetic_capture_on_save_post', 10, 3);

/**
 * Send the engram. Failures are logged to debug.log; they never block the save.
 */
function eidetic_capture_post_engram($settings, $engram) {
    $headers = array('Content-Type' => 'application/json');
    if (!empty($settings['token'])) {
        $headers['Authorization'] = 'Bearer ' . $settings['token'];
    }

    $response = wp_remote_post(
        $settings['daemon_url'] . '/engrams',
        array(
            'method'      => 'POST',
            'headers'     => $headers,
            'body'        => wp_json_encode($engram),
            'timeout'     => EIDETIC_CAPTURE_TIMEOUT,
            'blocking'    => true,
            'sslverify'   => true,
            'redirection' => 0,
        )
    );

    if (is_wp_error($response)) {
        eidetic_capture_log('post failed: ' . $response->get_error_message());
        return false;
    }
    $code = wp_remote_retrieve_response_code($response);
    if ($code < 200 || $code >= 300) {
        eidetic_capture_log('post non-2xx: HTTP ' . $code);
        return false;
    }
    return true;
}

/**
 * Single-line debug log helper. Only writes if WP_DEBUG_LOG is on.
 */
function eidetic_capture_log($message) {
    if (defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
        // phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_error_log
        error_log('[eidetic-capture] ' . $message);
    }
}

// ---------------------------------------------------------------------------
// Admin settings page (Settings → Eidetic)
// ---------------------------------------------------------------------------

function eidetic_capture_register_settings_page() {
    add_options_page(
        __('Eidetic', 'eidetic-capture'),
        __('Eidetic', 'eidetic-capture'),
        'manage_options',
        'eidetic-capture',
        'eidetic_capture_render_settings_page'
    );
}
add_action('admin_menu', 'eidetic_capture_register_settings_page');

function eidetic_capture_register_settings() {
    register_setting(
        'eidetic_capture',
        EIDETIC_CAPTURE_OPTION,
        array(
            'type'              => 'array',
            'sanitize_callback' => 'eidetic_capture_sanitize_settings',
            'default'           => array(),
        )
    );
}
add_action('admin_init', 'eidetic_capture_register_settings');

function eidetic_capture_sanitize_settings($input) {
    $out = array();
    $out['daemon_url']     = isset($input['daemon_url']) ? untrailingslashit(esc_url_raw($input['daemon_url'])) : EIDETIC_CAPTURE_DEFAULT_URL;
    $out['token']          = isset($input['token']) ? sanitize_text_field($input['token']) : '';
    $out['published_only'] = !empty($input['published_only']);
    return $out;
}

function eidetic_capture_render_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    $settings = eidetic_capture_get_settings();
    ?>
    <div class="wrap">
      <h1><?php esc_html_e('Eidetic Capture', 'eidetic-capture'); ?></h1>
      <p><?php esc_html_e('Captures saved posts as engrams in your local eideticd. Nothing leaves your machine unless you point the daemon URL at a remote bridge tunnel.', 'eidetic-capture'); ?></p>
      <form method="post" action="options.php">
        <?php settings_fields('eidetic_capture'); ?>
        <table class="form-table" role="presentation">
          <tr>
            <th scope="row"><label for="eidetic-daemon-url"><?php esc_html_e('Daemon URL', 'eidetic-capture'); ?></label></th>
            <td>
              <input name="<?php echo esc_attr(EIDETIC_CAPTURE_OPTION); ?>[daemon_url]" id="eidetic-daemon-url" type="url" class="regular-text" value="<?php echo esc_attr($settings['daemon_url']); ?>" placeholder="<?php echo esc_attr(EIDETIC_CAPTURE_DEFAULT_URL); ?>" />
              <p class="description"><?php esc_html_e('Default is http://127.0.0.1:8421 — the local bridge listener.', 'eidetic-capture'); ?></p>
            </td>
          </tr>
          <tr>
            <th scope="row"><label for="eidetic-token"><?php esc_html_e('Bearer token', 'eidetic-capture'); ?></label></th>
            <td>
              <input name="<?php echo esc_attr(EIDETIC_CAPTURE_OPTION); ?>[token]" id="eidetic-token" type="password" class="regular-text" value="<?php echo esc_attr($settings['token']); ?>" autocomplete="new-password" />
              <p class="description"><?php esc_html_e('Paste contents of ~/.eidetic/bridge-token. Stored in wp_options.', 'eidetic-capture'); ?></p>
            </td>
          </tr>
          <tr>
            <th scope="row"><?php esc_html_e('Capture scope', 'eidetic-capture'); ?></th>
            <td>
              <label>
                <input name="<?php echo esc_attr(EIDETIC_CAPTURE_OPTION); ?>[published_only]" type="checkbox" value="1" <?php checked($settings['published_only']); ?> />
                <?php esc_html_e('Capture published posts only (recommended)', 'eidetic-capture'); ?>
              </label>
              <p class="description"><?php esc_html_e('When off, drafts and pending posts are also sent.', 'eidetic-capture'); ?></p>
            </td>
          </tr>
        </table>
        <?php submit_button(); ?>
      </form>
      <hr />
      <h2><?php esc_html_e('Test connection', 'eidetic-capture'); ?></h2>
      <p><?php esc_html_e('Hits GET /healthz on the configured daemon URL.', 'eidetic-capture'); ?></p>
      <p>
        <button type="button" class="button button-secondary" id="eidetic-test-btn"><?php esc_html_e('Test connection', 'eidetic-capture'); ?></button>
        <span id="eidetic-test-result" style="margin-left:10px;"></span>
      </p>
      <script>
      (function () {
        var btn = document.getElementById('eidetic-test-btn');
        var out = document.getElementById('eidetic-test-result');
        if (!btn) return;
        btn.addEventListener('click', function () {
          out.textContent = '<?php echo esc_js(__('Testing…', 'eidetic-capture')); ?>';
          var data = new FormData();
          data.append('action', 'eidetic_capture_test');
          data.append('_ajax_nonce', '<?php echo esc_js(wp_create_nonce('eidetic_capture_test')); ?>');
          fetch(ajaxurl, { method: 'POST', credentials: 'same-origin', body: data })
            .then(function (r) { return r.json(); })
            .then(function (j) { out.textContent = (j && j.data) ? j.data : '<?php echo esc_js(__('Unknown response', 'eidetic-capture')); ?>'; })
            .catch(function (e) { out.textContent = 'Error: ' + e.message; });
        });
      })();
      </script>
    </div>
    <?php
}

/**
 * Admin-AJAX handler for the Test Connection button.
 */
function eidetic_capture_ajax_test() {
    if (!current_user_can('manage_options')) {
        wp_send_json_error(__('Insufficient permissions', 'eidetic-capture'));
    }
    check_ajax_referer('eidetic_capture_test');

    $settings = eidetic_capture_get_settings();
    $headers  = array();
    if (!empty($settings['token'])) {
        $headers['Authorization'] = 'Bearer ' . $settings['token'];
    }
    $response = wp_remote_get(
        $settings['daemon_url'] . '/healthz',
        array('headers' => $headers, 'timeout' => 3, 'sslverify' => true)
    );
    if (is_wp_error($response)) {
        wp_send_json_error('Error: ' . $response->get_error_message());
    }
    $code = wp_remote_retrieve_response_code($response);
    if ($code >= 200 && $code < 300) {
        wp_send_json_success('OK (HTTP ' . (int) $code . ')');
    }
    wp_send_json_error('HTTP ' . (int) $code);
}
add_action('wp_ajax_eidetic_capture_test', 'eidetic_capture_ajax_test');
