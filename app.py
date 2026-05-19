    with tab_qc:
        st.subheader("QC Dimension Report")
        st.caption("Every detected dimension is listed here for inspection review.")

        qc_report = build_qc_report(dimensions)
        qc_checked_items = []

        if dimensions:
            st.dataframe(
                qc_report,
                use_container_width=True
            )

            for index, item in enumerate(dimensions, start=1):
                callout = item.get("raw_text", "")
                dim_type = item.get("type", "").title()

                with st.expander(
                    f"QC-{index:03} | {dim_type} | {callout}"
                ):
                    measured_value = st.text_input(
                        "Measured value",
                        key=f"qc_measured_{index}"
                    )

                    pass_fail = st.selectbox(
                        "Pass / Fail",
                        ["Needs Check", "Pass", "Fail"],
                        key=f"qc_pass_fail_{index}"
                    )

                    notes = st.text_input(
                        "Inspector notes",
                        key=f"qc_notes_{index}"
                    )

                    qc_checked_items.append({
                        "qc_id": f"QC-{index:03}",
                        "dimension_type": dim_type,
                        "dimension_callout": callout,
                        "measured_value": measured_value,
                        "pass_fail": pass_fail,
                        "inspector_notes": notes
                    })

        else:
            st.info("No dimensions detected yet.")
