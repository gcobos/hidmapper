(print "Load server start ./festival_server.scm")
(set! server_port 1314)
(set! server_festival_version "festival" )
(set! server_log_file "./festival_server.log" )
(set! server_startup_file "" )

;; Marks end of machine created bit
;---


 ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
 ;; The default information below was created by the festival_server script
 ;; You should probably create a file which is similar but with whatever
 ;; access permissions and preloaded voices suit your local situation and
 ;; use the -c flag to festival_server

(defvar server_home ".")

;; Access from machines with no domain name and the local 
(set! server_access_list '("[^.]+" "127.0.0.1" "localhost.*" "asus"))

(cd server_home)
(set! default_access_strategy 'direct)

;; Load any voices you regularly use here, this will make the
;; server more responsive

; (voice_rab_diphone)
; (voice_gsw_diphone )
; (voice_ked_diphone)
; (voice_ked_mttilt_diphone)

