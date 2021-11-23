

symbols_splice_list = ['SBRF Splice', 'GOLD Splice', 'GAZR Splice', 'Si Splice', 'RTS Splice', 'ED Splice', 'Eu Splice',
                       'LKOH Splice', 'ROSN Splice', 'MXI Splice', 'VTBR Splice']
date_contracts = "-6.21"
symbols_fuchers_list = [f'SBRF{date_contracts}', f'GOLD{date_contracts}', f'GAZR{date_contracts}', f'Si{date_contracts}',
                        f'RTS{date_contracts}', f'ED{date_contracts}', f'Eu{date_contracts}', f'LKOH{date_contracts}',
                        f'ROSN{date_contracts}', f'MXI{date_contracts}', f'VTBR{date_contracts}']

symbols_splice_fuchers_dict = {'SBRF Splice': f'SBRF{date_contracts}', 'GOLD Splice': f'GOLD{date_contracts}',
                               'GAZR Splice': f'GAZR{date_contracts}', 'Si Splice': f'Si{date_contracts}',
                               'RTS Splice': f'RTS{date_contracts}', 'ED Splice': f'ED{date_contracts}',
                               'Eu Splice': f'Eu{date_contracts}', 'LKOH Splice': f'LKOH{date_contracts}',
                               'ROSN Splice': f'ROSN{date_contracts}', 'MXI Splice': f'MXI{date_contracts}',
                               'VTBR Splice': f'VTBR{date_contracts}'}

fuchers_code_to_fuchers_name = {'SR': 'SBRF', 'GD': 'GOLD', 'GZ': 'GAZR', 'Si': 'Si', 'Ri': 'RTS', 'ED': 'ED',
                                'Eu': 'Eu', 'LH': 'LKOH', 'RN': 'ROSN'}
fuchers_mcode_to_fuchers_month = {'H': 3, 'M': 6, 'U': 9, 'Z': 12}
fuchers_fuchers_month_to_mcode = {3: 'H', 6: 'M', 9: 'U', 12: 'Z'}
