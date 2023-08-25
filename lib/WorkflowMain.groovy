// This file is based on the nf-core/tools pipeline-template.
// Changes to this file must be propagated via wf-template.

class WorkflowMain {

    // Citation string for pipeline
    public static String citation(workflow) {
        return "If you use ${workflow.manifest.name} for your analysis please cite:\n\n" +
            "* The nf-core framework\n" +
            "  https://doi.org/10.1038/s41587-020-0439-x\n\n"
    }

    // Generate help string
    public static String help(workflow, params, log) {
        String line_sep = ' \\ \n\t'
        String command_example = params.wf.example_cmd.join(line_sep)
        String command = 'nextflow run ' + workflow.manifest.name + line_sep + command_example
        String help_string = ''
        help_string += NfcoreTemplate.logo(workflow, params.monochrome_logs)
        help_string += NfcoreSchema.paramsHelp(workflow, params, command)
        help_string += '\n' + citation(workflow) + '\n'
        return help_string
    }

    // Generate parameter summary log string
    public static String paramsSummaryLog(workflow, params, log) {
        String workflow_version = NfcoreTemplate.version(workflow)
        String summary_log = ''
        summary_log += NfcoreTemplate.logo(workflow, params.monochrome_logs)
        summary_log += NfcoreSchema.paramsSummaryLog(workflow, params)
        summary_log += '\n' + citation(workflow) + '\n'
        summary_log += NfcoreTemplate.dashedLine(params.monochrome_logs)
        summary_log += "\nThis is ${workflow.manifest.name} ${workflow_version}.\n"
        summary_log += NfcoreTemplate.dashedLine(params.monochrome_logs)
        return summary_log
    }

    public static Map validateThreads(workflow, params, log) {

        // attempt to determine if the executor is local
        // we do this by inspecting the config for process.executor
        // this is reasonable as we only set one executor for our workflows currently
        def global_executor = workflow.session.config?.process?.executor ?: "local"
        Integer max_local_threads = Integer.MAX_VALUE
        if (global_executor == "local") {
            // attempt to pull local executor setting from config and fall back to
            // number of local CPUs if not found
            max_local_threads = workflow.session.config?.executor?.$local?.cpus ?: \
                Runtime.getRuntime().availableProcessors()
            log.info("Local thread limit appears to be ${max_local_threads}.")
        }

        Boolean bad_threads = false
        def result = []
        // find explicit closures
        Map thread_map = workflow.session.config?.epi2melabs?.threading ?: [:]
        // and regular looking thready params
        //TODO we may wish to define a threads "namespace" to ensure nothing gets sucked up here
        thread_map += params.findAll({it.key.contains("threads") && it.key != "validate_threads"})
        // determine exceeding threshold
        thread_map.each { param, v ->
            Integer this_threads = null
            Boolean is_auto = v instanceof Map && v.containsKey("clj") && v.clj instanceof Closure
            String auto_hint = ""
            if (is_auto) {
                this_threads = v.clj.call(params)
                auto_hint = v["hint"] ? v.hint.call(params, this_threads) : ""
            }
            else if(v instanceof Integer) {
                this_threads = v
            }
            if (this_threads) {
                result << [
                    name: param,
                    threads: this_threads,
                    exceeds: this_threads > max_local_threads,
                    auto: is_auto,
                    auto_hint: auto_hint,
                ]
                if (this_threads > max_local_threads) {
                    bad_threads = true
                }
            }
        }
        return [
            executor: global_executor,
            thread_limit: max_local_threads,
            processes: result,
            bad_threads: bad_threads,
        ]
    }

    public static void printValidateThreads(result, log, monochrome_logs) {
        Map colors = NfcoreTemplate.logColours(monochrome_logs)

        // thread check header
        String stderr_msg = "${colors.bold}Thread check:${colors.reset}\n"
        stderr_msg += "  ${colors.yellow}executor: ${colors.reset}${result.executor}\n"
        String thread_limit = result.executor == "local" ? result.thread_limit.toString() : "NA"
        stderr_msg += "  ${colors.yellow}threads : ${colors.reset}${thread_limit}\n"

        // build exceeds (or not) messages for all processes
        // then split based on whether the threading is calculated by us automatically
        // via a closure, or is a manual user entered parameter
        Integer max_name = result.processes.collect({it.name.size()}).max()
        def (auto_proc, manual_proc) = result.processes.collect { data ->
            String msg = ""
            String c = colors.green
            if (data.exceeds) {
                msg = " exceeds thread limit of ${result.thread_limit}"
                c = colors.red
            }
            [data, msg, c]
        }.split { data, msg, c -> data.auto }

        if (auto_proc) {
            stderr_msg += "${colors.bold}Automated threading options:${colors.reset}\n"
            auto_proc.each { data, msg, c ->
                stderr_msg += "  ${colors.yellow}${data.name}:\n"
                stderr_msg += "    threads : ${c}${data.threads}${msg}${colors.reset}\n"
                if(data.auto_hint) {
                    stderr_msg += "    ${colors.yellow}tip     : ${colors.reset}${data.auto_hint}\n"
                }
            }
        }
        if (manual_proc) {
            stderr_msg += "${colors.bold}Manual threading options:${colors.reset}\n"
            manual_proc.each { data, msg, c ->
                stderr_msg += "  " + colors.yellow + data.name.padRight(max_name) + ": " + \
                    c + data.threads + msg + colors.reset + '\n'
            }
        }
        log.info stderr_msg
    }

    // Validate parameters and print summary to screen
    public static void initialise(workflow, params, log) {
        // init colors helper
        Map colors = NfcoreTemplate.logColours(params.monochrome_logs)

        // Print help to screen if required
        if (params.help) {
            log.info help(workflow, params, log)
            System.exit(0)
        }

        // Print workflow version and exit on --version
        if (params.version) {
            String workflow_version = NfcoreTemplate.version(workflow)
            log.info "${workflow.manifest.name} ${workflow_version}"
            System.exit(0)
        }

        // Explode on conda
        // conda.enabled seems to be backward compatible but wrap this
        // in a generic catch just in case
        try {
            if (workflow.session.config.conda.enabled) {
                log.error "Sorry, this workflow is not compatible with Conda, please use -profile standard (Docker) or -profile singularity."
                System.exit(1)
            }
        } catch(Exception e) {}

        // Validate workflow parameters via the JSON schema
        if (params.validate_params) {
            NfcoreSchema.validateParameters(workflow, params, log)
        }

        // Validate thread counting
        if (params.validate_threads) {
            def result = validateThreads(workflow, params, log)
            if (result.bad_threads) {
                printValidateThreads(result, log, params.monochrome_logs)
                log.error "Validation of thread parameters failed!\nPlease readjust the threading parameters highlighted above.\n${colors.reset}${colors.dim}- Ignore thread errors: --validate_threads false${colors.reset}"
                System.exit(1)
            }
        }

        // Print parameter summary log to screen
        log.info paramsSummaryLog(workflow, params, log)
    }
}
