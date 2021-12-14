\* Source Pyomo model name=Model *\

min 
objective:
+0 ONE_VAR_CONSTANT

s.t.

c_e_Bus_balance(ch4_0)_:
+1 flow(m_reactor_storage_products_ch4_0)
= 0

c_e_Bus_balance(ch4_1)_:
+1 flow(m_reactor_storage_products_ch4_1)
= 0

c_e_Bus_balance(ch4_2)_:
+1 flow(m_reactor_storage_products_ch4_2)
= 0

c_e_Bus_balance(h2_co2_0)_:
+1 flow(h2_co2_m_reactor_combine_educts_0)
= 0

c_e_Bus_balance(h2_co2_1)_:
+1 flow(h2_co2_m_reactor_combine_educts_1)
= 0

c_e_Bus_balance(h2_co2_2)_:
+1 flow(h2_co2_m_reactor_combine_educts_2)
= 0

c_e_Transformer_relation(m_reactor_m_reactor_storage_educts_m_reactor_storage_products_0)_:
-1.075268817204301 flow(m_reactor_m_reactor_storage_products_0)
+1 flow(m_reactor_storage_educts_m_reactor_0)
= 0

c_e_Transformer_relation(m_reactor_m_reactor_storage_educts_m_reactor_storage_products_1)_:
-1.075268817204301 flow(m_reactor_m_reactor_storage_products_1)
+1 flow(m_reactor_storage_educts_m_reactor_1)
= 0

c_e_Transformer_relation(m_reactor_m_reactor_storage_educts_m_reactor_storage_products_2)_:
-1.075268817204301 flow(m_reactor_m_reactor_storage_products_2)
+1 flow(m_reactor_storage_educts_m_reactor_2)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_co2_m_reactor_storage_educts_0)_:
+5 flow(co2_m_reactor_combine_educts_0)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_0)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_co2_m_reactor_storage_educts_1)_:
+5 flow(co2_m_reactor_combine_educts_1)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_1)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_co2_m_reactor_storage_educts_2)_:
+5 flow(co2_m_reactor_combine_educts_2)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_2)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_h2_co2_m_reactor_storage_educts_0)_:
+1.25 flow(h2_co2_m_reactor_combine_educts_0)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_0)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_h2_co2_m_reactor_storage_educts_1)_:
+1.25 flow(h2_co2_m_reactor_combine_educts_1)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_1)
= 0

c_e_Transformer_relation(m_reactor_combine_educts_h2_co2_m_reactor_storage_educts_2)_:
+1.25 flow(h2_co2_m_reactor_combine_educts_2)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_2)
= 0

c_e_GenericStorageBlock_balance_first(m_reactor_storage_educts)_:
+1 GenericStorageBlock_capacity(m_reactor_storage_educts_0)
-1 GenericStorageBlock_init_cap(m_reactor_storage_educts)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_0)
+1 flow(m_reactor_storage_educts_m_reactor_0)
= 0

c_e_GenericStorageBlock_balance_first(m_reactor_storage_products)_:
+1 GenericStorageBlock_capacity(m_reactor_storage_products_0)
-1 GenericStorageBlock_init_cap(m_reactor_storage_products)
-1 flow(m_reactor_m_reactor_storage_products_0)
+1 flow(m_reactor_storage_products_ch4_0)
= 0

c_e_GenericStorageBlock_balance(m_reactor_storage_educts_1)_:
-1 GenericStorageBlock_capacity(m_reactor_storage_educts_0)
+1 GenericStorageBlock_capacity(m_reactor_storage_educts_1)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_1)
+1 flow(m_reactor_storage_educts_m_reactor_1)
= 0

c_e_GenericStorageBlock_balance(m_reactor_storage_educts_2)_:
-1 GenericStorageBlock_capacity(m_reactor_storage_educts_1)
+1 GenericStorageBlock_capacity(m_reactor_storage_educts_2)
-1 flow(m_reactor_combine_educts_m_reactor_storage_educts_2)
+1 flow(m_reactor_storage_educts_m_reactor_2)
= 0

c_e_GenericStorageBlock_balance(m_reactor_storage_products_1)_:
-1 GenericStorageBlock_capacity(m_reactor_storage_products_0)
+1 GenericStorageBlock_capacity(m_reactor_storage_products_1)
-1 flow(m_reactor_m_reactor_storage_products_1)
+1 flow(m_reactor_storage_products_ch4_1)
= 0

c_e_GenericStorageBlock_balance(m_reactor_storage_products_2)_:
-1 GenericStorageBlock_capacity(m_reactor_storage_products_1)
+1 GenericStorageBlock_capacity(m_reactor_storage_products_2)
-1 flow(m_reactor_m_reactor_storage_products_2)
+1 flow(m_reactor_storage_products_ch4_2)
= 0

c_e_GenericStorageBlock_balanced_cstr(m_reactor_storage_educts)_:
+1 GenericStorageBlock_capacity(m_reactor_storage_educts_2)
-1 GenericStorageBlock_init_cap(m_reactor_storage_educts)
= 0

c_e_GenericStorageBlock_balanced_cstr(m_reactor_storage_products)_:
+1 GenericStorageBlock_capacity(m_reactor_storage_products_2)
-1 GenericStorageBlock_init_cap(m_reactor_storage_products)
= 0

c_e_ONE_VAR_CONSTANT: 
ONE_VAR_CONSTANT = 1.0

bounds
   0 <= flow(co2_m_reactor_combine_educts_0) <= +inf
   0 <= flow(co2_m_reactor_combine_educts_1) <= +inf
   0 <= flow(co2_m_reactor_combine_educts_2) <= +inf
   0 <= flow(h2_co2_m_reactor_combine_educts_0) <= +inf
   0 <= flow(h2_co2_m_reactor_combine_educts_1) <= +inf
   0 <= flow(h2_co2_m_reactor_combine_educts_2) <= +inf
   0 <= flow(m_reactor_m_reactor_storage_products_0) <= 5
   0 <= flow(m_reactor_m_reactor_storage_products_1) <= 5
   0 <= flow(m_reactor_m_reactor_storage_products_2) <= 5
   0 <= flow(m_reactor_combine_educts_m_reactor_storage_educts_0) <= 50
   0 <= flow(m_reactor_combine_educts_m_reactor_storage_educts_1) <= 50
   0 <= flow(m_reactor_combine_educts_m_reactor_storage_educts_2) <= 50
   0 <= flow(m_reactor_storage_educts_m_reactor_0) <= +inf
   0 <= flow(m_reactor_storage_educts_m_reactor_1) <= +inf
   0 <= flow(m_reactor_storage_educts_m_reactor_2) <= +inf
   0 <= flow(m_reactor_storage_products_ch4_0) <= 50
   0 <= flow(m_reactor_storage_products_ch4_1) <= 50
   0 <= flow(m_reactor_storage_products_ch4_2) <= 50
   0 <= GenericStorageBlock_capacity(m_reactor_storage_educts_0) <= 1000
   0 <= GenericStorageBlock_capacity(m_reactor_storage_educts_1) <= 1000
   0 <= GenericStorageBlock_capacity(m_reactor_storage_educts_2) <= 1000
   0 <= GenericStorageBlock_capacity(m_reactor_storage_products_0) <= 1000
   0 <= GenericStorageBlock_capacity(m_reactor_storage_products_1) <= 1000
   0 <= GenericStorageBlock_capacity(m_reactor_storage_products_2) <= 1000
   0 <= GenericStorageBlock_init_cap(m_reactor_storage_educts) <= 1000
   0 <= GenericStorageBlock_init_cap(m_reactor_storage_products) <= 1000
end
